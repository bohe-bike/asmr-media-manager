import os
import shutil
import logging

from app.utils.file_utils import sanitize_filename, resolve_conflict

logger = logging.getLogger(__name__)


class OrganizeService:
    """整理输出服务：将媒体文件移动到整理目录，按作者归档"""

    def __init__(self, library_dir: str):
        self.library_dir = library_dir

    def move_to_library(self, media) -> str:
        """将媒体文件移动到整理目录的作者名下，返回新路径"""
        author = media.creator or media.cv or "未分类"
        author_dir = os.path.join(self.library_dir, sanitize_filename(author))
        os.makedirs(author_dir, exist_ok=True)

        new_name = self._build_filename(media)
        new_path = os.path.join(author_dir, new_name)
        new_path = resolve_conflict(new_path)

        shutil.move(media.file_path, new_path)

        # Move associated files
        self._move_associated_files(media.file_path, new_path)

        return new_path

    def _build_filename(self, media) -> str:
        ext = os.path.splitext(media.file_name)[1]
        if media.media_type == "audio":
            parts = []
            if media.cv:
                parts.append(f"[{media.cv}]")
            if media.title:
                parts.append(media.title)
            if media.rj_id:
                parts.append(f"({media.rj_id})")
        else:
            parts = []
            if media.creator:
                parts.append(f"[{media.creator}]")
            if media.title:
                parts.append(media.title)

        name = " ".join(parts) if parts else os.path.splitext(media.file_name)[0]
        name = sanitize_filename(name)
        return name + ext

    def _move_associated_files(self, old_path: str, new_path: str) -> None:
        """移动关联文件（封面、NFO 等）"""
        old_dir = os.path.dirname(old_path)
        new_dir = os.path.dirname(new_path)

        for filename in os.listdir(old_dir):
            if filename.lower() in ("cover.jpg", "cover.jpeg", "cover.png", "folder.jpg", "nfo"):
                src = os.path.join(old_dir, filename)
                dst = os.path.join(new_dir, filename)
                if os.path.isfile(src) and not os.path.exists(dst):
                    try:
                        shutil.copy2(src, dst)
                    except Exception as e:
                        logger.warning(f"Failed to copy associated file {src}: {e}")
