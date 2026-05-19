import pytest
from app.utils.file_utils import (
    get_media_type,
    get_format,
    is_supported_format,
    sanitize_filename,
    resolve_conflict,
)


class TestMediaType:
    def test_audio_mp3(self):
        assert get_media_type("song.mp3") == "audio"

    def test_audio_flac(self):
        assert get_media_type("song.flac") == "audio"

    def test_video_mp4(self):
        assert get_media_type("video.mp4") == "video"

    def test_video_mkv(self):
        assert get_media_type("video.mkv") == "video"

    def test_unknown(self):
        assert get_media_type("file.txt") is None


class TestFormat:
    def test_mp3(self):
        assert get_format("song.MP3") == "mp3"

    def test_flac(self):
        assert get_format("path/to/song.flac") == "flac"


class TestSupportedFormat:
    def test_supported_audio(self):
        assert is_supported_format("song.flac") is True

    def test_supported_video(self):
        assert is_supported_format("video.mp4") is True

    def test_unsupported(self):
        assert is_supported_format("file.txt") is False

    def test_unsupported_exe(self):
        assert is_supported_format("file.exe") is False


class TestSanitizeFilename:
    def test_remove_invalid_chars(self):
        result = sanitize_filename('file<>:"/\\|?*name')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result

    def test_multiple_spaces(self):
        result = sanitize_filename("file   name")
        assert "  " not in result

    def test_max_length(self):
        long_name = "a" * 300
        result = sanitize_filename(long_name, max_length=200)
        assert len(result) <= 200


class TestResolveConflict:
    def test_no_conflict(self, tmp_path):
        path = str(tmp_path / "new_file.flac")
        assert resolve_conflict(path) == path
