import os
import shutil
import logging

from app.utils.file_utils import sanitize_filename, resolve_conflict

logger = logging.getLogger(__name__)


class OrganizeService:
    """整理输出服务：将媒体文件移动到整理目录，按 作者/作品 目录结构归档。

    目标结构（Plex 音乐库友好）：
        library/
        └── 作者名/
            └── [RJ123456] 作品标题/
                ├── 文件.mp3
                └── cover.jpg
    """

    def __init__(self, library_dir: str):
        self.library_dir = library_dir

    def move_to_library(self, media) -> str:
        """将媒体文件移动到整理目录的 作者/作品 目录下，返回新路径。"""
        author = media.creator or media.circle or media.cv or "未分类"
        author_dir = os.path.join(self.library_dir, sanitize_filename(author))

        # 构建作品目录名
        album_dir_name = self._build_album_dir_name(media)
        album_dir = os.path.join(author_dir, album_dir_name)
        os.makedirs(album_dir, exist_ok=True)

        # 构建文件名
        new_name = self._build_filename(media)
        new_path = os.path.join(album_dir, new_name)
        new_path = resolve_conflict(new_path)

        shutil.move(media.file_path, new_path)

        # 移动关联文件（封面、NFO 等）到作品目录
        self._move_associated_files(media.file_path, new_path)

        return new_path

    def preview(self, media) -> dict:
        """预览整理后的目标路径，不实际移动文件。"""
        author = media.creator or media.circle or media.cv or "未分类"
        author_dir = os.path.join(self.library_dir, sanitize_filename(author))

        album_dir_name = self._build_album_dir_name(media)
        album_dir = os.path.join(author_dir, album_dir_name)

        new_name = self._build_filename(media)
        new_path = os.path.join(album_dir, new_name)
        conflict = os.path.exists(new_path) and new_path != media.file_path

        return {
            "old_path": media.file_path,
            "new_path": new_path,
            "author_dir": author_dir,
            "album_dir": album_dir,
            "conflict": conflict,
        }

    def _build_album_dir_name(self, media) -> str:
        """构建作品目录名：[RJ号] 标题"""
        parts = []
        if media.rj_id:
            parts.append(f"[{media.rj_id}]")
        elif media.dl_id:
            parts.append(f"[{media.dl_id}]")
        if media.title:
            parts.append(media.title)

        if parts:
            return sanitize_filename(" ".join(parts), max_length=150)

        # 降级：用文件名（去掉扩展名）
        return sanitize_filename(os.path.splitext(media.file_name)[0], max_length=150)

    def _build_filename(self, media) -> str:
        """构建文件名。"""
        ext = os.path.splitext(media.file_name)[1]

        # 如果有标题，用简洁文件名（不需要包含作者/作品信息，因为已经在目录名里了）
        if media.title:
            name = media.title
            if media.cv:
                name = f"[{media.cv}] {name}"
            if media.rj_id:
                name = f"{name} ({media.rj_id})"
        else:
            # 保持原文件名
            name = os.path.splitext(media.file_name)[0]

        name = sanitize_filename(name, max_length=200)
        return name + ext

    def _move_associated_files(self, old_path: str, new_path: str) -> None:
        """移动关联文件（封面、NFO 等）到目标目录。"""
        old_dir = os.path.dirname(old_path)
        new_dir = os.path.dirname(new_path)

        associated_names = {
            "cover.jpg", "cover.jpeg", "cover.png",
            "folder.jpg", "folder.jpeg", "front.jpg",
        }

        # 也移动同名的 NFO 文件
        old_base = os.path.splitext(os.path.basename(old_path))[0]
        nfo_name = f"{old_base}.nfo"

        for filename in os.listdir(old_dir):
            if filename.lower() in associated_names or filename == nfo_name:
                src = os.path.join(old_dir, filename)
                dst = os.path.join(new_dir, filename)
                if os.path.isfile(src) and not os.path.exists(dst):
                    try:
                        shutil.copy2(src, dst)
                    except Exception as e:
                        logger.warning(f"Failed to copy associated file {src}: {e}")
