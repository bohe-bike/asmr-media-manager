import os
import logging
from pathlib import Path

import httpx

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

    async def download_cover(self, url: str, save_dir: str) -> str | None:
        """从远程 URL 下载封面图片到指定目录。

        返回保存的文件路径，失败返回 None。
        """
        try:
            proxy = self.settings.dlsite_proxy or None
            async with httpx.AsyncClient(
                timeout=15.0,
                proxy=proxy,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://www.dlsite.com/",
                },
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()

            # 根据 Content-Type 决定扩展名
            content_type = resp.headers.get("content-type", "")
            if "png" in content_type:
                ext = ".png"
            else:
                ext = ".jpg"

            os.makedirs(save_dir, exist_ok=True)
            cover_path = os.path.join(save_dir, f"cover{ext}")
            with open(cover_path, "wb") as f:
                f.write(resp.content)

            logger.info(f"Downloaded cover to {cover_path}")
            return cover_path
        except Exception as e:
            logger.warning(f"Failed to download cover from {url}: {e}")
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
