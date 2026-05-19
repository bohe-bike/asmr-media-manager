import os
import shutil
import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media
from app.schemas.rename import (
    RenamePreviewItem,
    RenamePreviewResponse,
    RenameResultItem,
    RenameExecuteResponse,
)
from app.utils.file_utils import sanitize_filename, resolve_conflict
from app.config import get_settings

logger = logging.getLogger(__name__)


class RenameService:
    """重命名服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def preview(
        self, media_list: list[Media], pattern: str | None = None
    ) -> RenamePreviewResponse:
        """预览重命名操作"""
        items = []
        conflicts = []

        for media in media_list:
            old_path = media.file_path
            new_name = self._build_filename(media, pattern)
            new_dir = os.path.dirname(old_path)
            new_path = os.path.join(new_dir, new_name)

            conflict = os.path.exists(new_path) and new_path != old_path
            if conflict:
                conflicts.append({"media_id": media.id, "path": new_path})

            items.append(
                RenamePreviewItem(
                    media_id=media.id,
                    old_path=old_path,
                    new_path=new_path,
                    new_dir=new_dir,
                    conflict=conflict,
                )
            )

        return RenamePreviewResponse(items=items, conflicts=conflicts, total=len(items))

    async def execute(
        self,
        media_list: list[Media],
        pattern: str | None = None,
        move_cover: bool = True,
    ) -> RenameExecuteResponse:
        """执行重命名操作"""
        success = 0
        failed = 0
        results = []

        for media in media_list:
            try:
                old_path = media.file_path
                new_name = self._build_filename(media, pattern)
                new_dir = os.path.dirname(old_path)
                new_path = os.path.join(new_dir, new_name)
                new_path = resolve_conflict(new_path)

                os.makedirs(new_dir, exist_ok=True)
                shutil.move(old_path, new_path)

                # Move cover if exists
                if move_cover and media.cover_path and os.path.exists(media.cover_path):
                    cover_dir = os.path.dirname(new_path)
                    new_cover = os.path.join(cover_dir, os.path.basename(media.cover_path))
                    if media.cover_path != new_cover:
                        shutil.move(media.cover_path, new_cover)
                        media.cover_path = new_cover

                media.file_path = new_path
                media.file_name = os.path.basename(new_path)
                media.status = "renamed"

                success += 1
                results.append(
                    RenameResultItem(
                        media_id=media.id,
                        old_path=old_path,
                        new_path=new_path,
                        status="success",
                    )
                )
            except Exception as e:
                logger.error(f"Failed to rename media {media.id}: {e}")
                failed += 1
                results.append(
                    RenameResultItem(
                        media_id=media.id,
                        old_path=media.file_path,
                        new_path="",
                        status="failed",
                    )
                )

        await self.db.commit()
        return RenameExecuteResponse(success=success, failed=failed, results=results)

    def _build_filename(self, media: Media, pattern: str | None = None) -> str:
        """根据媒体类型和元数据生成文件名"""
        ext = os.path.splitext(media.file_name)[1]

        if pattern:
            name = pattern
            name = name.replace("{cv}", media.cv or "")
            name = name.replace("{title}", media.title or "")
            name = name.replace("{rj_id}", media.rj_id or "")
            name = name.replace("{creator}", media.creator or "")
            name = name.replace("{circle}", media.circle or "")
            name = name.replace("{dl_id}", media.dl_id or "")
        elif media.media_type == "audio":
            name = self._build_audio_name(media)
        else:
            name = self._build_video_name(media)

        name = sanitize_filename(name, self.settings.max_filename_length)
        return name + ext

    def _build_audio_name(self, media: Media) -> str:
        parts = []
        if media.cv:
            parts.append(f"[{media.cv}]")
        if media.title:
            parts.append(media.title)
        if media.rj_id:
            parts.append(f"({media.rj_id})")
        return " ".join(parts) if parts else os.path.splitext(media.file_name)[0]

    def _build_video_name(self, media: Media) -> str:
        parts = []
        if media.creator:
            parts.append(f"[{media.creator}]")
        if media.title:
            parts.append(media.title)
        return " ".join(parts) if parts else os.path.splitext(media.file_name)[0]
