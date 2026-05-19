import os
import logging
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)


class CoverService:
    """封面管理服务"""

    def __init__(self):
        self.settings = get_settings()

    async def find_local_cover(self, media_path: str) -> str | None:
        """在媒体目录中查找封面图片"""
        media_dir = os.path.dirname(media_path)
        for name in self.settings.cover_filenames:
            cover_path = os.path.join(media_dir, name)
            if os.path.isfile(cover_path):
                return cover_path
        return None

    async def extract_from_video(self, video_path: str, timestamp: float = 10.0) -> str | None:
        """从视频中截取帧作为封面"""
        try:
            output_dir = os.path.dirname(video_path)
            output_path = os.path.join(output_dir, "cover.jpg")

            cmd = [
                "ffmpeg", "-y",
                "-ss", str(timestamp),
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                output_path,
            ]

            import subprocess
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
        except Exception as e:
            logger.warning(f"Failed to extract cover from video {video_path}: {e}")
        return None
