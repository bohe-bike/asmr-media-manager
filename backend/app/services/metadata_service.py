import os
import logging
from pathlib import Path

from app.utils.file_utils import get_media_type
from app.utils.text_utils import split_artist

logger = logging.getLogger(__name__)


class MetadataService:
    """元数据读写服务"""

    async def read_metadata(self, file_path: str) -> dict:
        """读取媒体文件元数据"""
        media_type = get_media_type(file_path)
        if media_type == "audio":
            return await self.read_audio_metadata(file_path)
        elif media_type == "video":
            return await self.read_video_metadata(file_path)
        return {}

    async def read_audio_metadata(self, file_path: str) -> dict:
        """使用 Mutagen 读取音频文件元数据"""
        try:
            from mutagen import File as MutagenFile
            from mutagen.flac import FLAC
            from mutagen.mp3 import MP3
            from mutagen.mp4 import MP4
            from mutagen.id3 import ID3

            result = {
                "duration": None,
                "bitrate": None,
                "sample_rate": None,
                "channels": None,
                "title": None,
                "artist": None,
                "album": None,
                "genre": None,
            }

            audio = MutagenFile(file_path)
            if audio is None:
                return result

            result["duration"] = audio.info.length if hasattr(audio.info, "length") else None
            result["bitrate"] = getattr(audio.info, "bitrate", None)
            result["sample_rate"] = getattr(audio.info, "sample_rate", None)
            result["channels"] = getattr(audio.info, "channels", None)

            # Read tags
            if hasattr(audio, "tags") and audio.tags:
                tags = audio.tags
                # Try common tag formats
                if isinstance(tags, ID3):
                    result["title"] = str(tags.get("TIT2", "")) or None
                    raw_artist = str(tags.get("TPE1", "")) or None
                    result["artist"] = split_artist(raw_artist) if raw_artist else None
                    result["album"] = str(tags.get("TALB", "")) or None
                    result["genre"] = str(tags.get("TCON", "")) or None
                elif hasattr(tags, "get"):
                    result["title"] = str(tags.get("title", [""])[0]) or None
                    raw_artist = str(tags.get("artist", [""])[0]) or None
                    result["artist"] = split_artist(raw_artist) if raw_artist else None
                    result["album"] = str(tags.get("album", [""])[0]) or None
                    result["genre"] = str(tags.get("genre", [""])[0]) or None

            return result
        except Exception as e:
            logger.warning(f"Failed to read audio metadata for {file_path}: {e}")
            return {}

    async def read_video_metadata(self, file_path: str) -> dict:
        """使用 pymediainfo 读取视频文件元数据"""
        try:
            from pymediainfo import MediaInfo

            result = {
                "duration": None,
                "bitrate": None,
                "width": None,
                "height": None,
                "title": None,
            }

            media_info = MediaInfo.parse(file_path)

            for track in media_info.tracks:
                if track.track_type == "General":
                    result["duration"] = track.duration / 1000.0 if track.duration else None
                    result["title"] = track.title or None
                    if track.overall_bit_rate:
                        result["bitrate"] = int(track.overall_bit_rate / 1000)
                elif track.track_type == "Video":
                    result["width"] = track.width
                    result["height"] = track.height

            return result
        except Exception as e:
            logger.warning(f"Failed to read video metadata for {file_path}: {e}")
            return {}

    async def write_audio_tags(self, file_path: str, tags: dict, cover_path: str | None = None) -> bool:
        """将标签写入音频文件，支持 MP3/FLAC/M4A/OPUS/OGG。

        tags: title, artist, album_artist, genre, comment
        cover_path: 封面图片路径（可选）
        """
        try:
            from mutagen import File as MutagenFile
            from mutagen.flac import FLAC, Picture
            from mutagen.mp3 import MP3
            from mutagen.mp4 import MP4, MP4Cover
            from mutagen.id3 import TIT2, TPE1, TPE2, TCON, COMM, APIC
            from mutagen.oggopus import OggOpus
            from mutagen.oggvorbis import OggVorbis

            audio = MutagenFile(file_path)
            if audio is None:
                return False

            # 读取封面数据
            cover_data = None
            cover_mime = "image/jpeg"
            if cover_path and os.path.isfile(cover_path):
                with open(cover_path, "rb") as f:
                    cover_data = f.read()
                if cover_path.lower().endswith(".png"):
                    cover_mime = "image/png"

            if isinstance(audio, MP3):
                if audio.tags is None:
                    audio.add_tags()
                if "title" in tags:
                    audio.tags["TIT2"] = TIT2(encoding=3, text=tags["title"])
                if "artist" in tags:
                    audio.tags["TPE1"] = TPE1(encoding=3, text=tags["artist"])
                if "album_artist" in tags:
                    audio.tags["TPE2"] = TPE2(encoding=3, text=tags["album_artist"])
                if "genre" in tags:
                    audio.tags["TCON"] = TCON(encoding=3, text=tags["genre"])
                if "comment" in tags:
                    audio.tags["COMM"] = COMM(encoding=3, lang="eng", text=tags["comment"])
                if cover_data:
                    audio.tags.add(APIC(
                        encoding=3, mime=cover_mime, type=3, desc="Cover", data=cover_data
                    ))

            elif isinstance(audio, FLAC):
                if "title" in tags:
                    audio["TITLE"] = tags["title"]
                if "artist" in tags:
                    audio["ARTIST"] = tags["artist"]
                if "album_artist" in tags:
                    audio["ALBUMARTIST"] = tags["album_artist"]
                if "genre" in tags:
                    audio["GENRE"] = tags["genre"]
                if "comment" in tags:
                    audio["COMMENT"] = tags["comment"]
                if cover_data:
                    pic = Picture()
                    pic.type = 3  # Cover (front)
                    pic.mime = cover_mime
                    pic.desc = "Cover"
                    pic.data = cover_data
                    audio.clear_pictures()
                    audio.add_picture(pic)

            elif isinstance(audio, MP4):
                if "title" in tags:
                    audio["\xa9nam"] = [tags["title"]]
                if "artist" in tags:
                    audio["\xa9ART"] = [tags["artist"]]
                if "album_artist" in tags:
                    audio["aART"] = [tags["album_artist"]]
                if "genre" in tags:
                    audio["\xa9gen"] = [tags["genre"]]
                if "comment" in tags:
                    audio["\xa9cmt"] = [tags["comment"]]
                if cover_data:
                    fmt = MP4Cover.FORMAT_PNG if cover_mime == "image/png" else MP4Cover.FORMAT_JPEG
                    audio["covr"] = [MP4Cover(cover_data, imageformat=fmt)]

            elif isinstance(audio, (OggOpus, OggVorbis)):
                if "title" in tags:
                    audio["title"] = [tags["title"]]
                if "artist" in tags:
                    audio["artist"] = [tags["artist"]]
                if "album_artist" in tags:
                    audio["albumartist"] = [tags["album_artist"]]
                if "genre" in tags:
                    audio["genre"] = [tags["genre"]]
                if "comment" in tags:
                    audio["comment"] = [tags["comment"]]
                if cover_data:
                    pic = Picture()
                    pic.type = 3
                    pic.mime = cover_mime
                    pic.desc = "Cover"
                    pic.data = cover_data
                    from base64 import b64encode
                    audio["metadata_block_picture"] = [b64encode(pic.write()).decode("ascii")]

            audio.save()
            return True
        except Exception as e:
            logger.error(f"Failed to write audio tags for {file_path}: {e}")
            return False
