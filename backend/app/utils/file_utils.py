import os
import re
from pathlib import Path

from app.core.constants import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS, MEDIA_EXTENSIONS


def get_media_type(file_path: str) -> str | None:
    ext = Path(file_path).suffix.lower().lstrip(".")
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    elif ext in VIDEO_EXTENSIONS:
        return "video"
    return None


def get_format(file_path: str) -> str:
    return Path(file_path).suffix.lower().lstrip(".")


def is_supported_format(file_path: str) -> bool:
    ext = Path(file_path).suffix.lower().lstrip(".")
    return ext in MEDIA_EXTENSIONS


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """清理文件名中的非法字符"""
    # Remove characters invalid on Windows/Linux
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace multiple spaces with single
    name = re.sub(r'\s+', ' ', name).strip()
    # Truncate
    if len(name) > max_length:
        name = name[:max_length].rstrip()
    return name


def resolve_conflict(path: str) -> str:
    """文件名冲突时自动加序号"""
    if not os.path.exists(path):
        return path

    base, ext = os.path.splitext(path)
    counter = 2
    while os.path.exists(f"{base} ({counter}){ext}"):
        counter += 1
    return f"{base} ({counter}){ext}"


def safe_move(src: str, dst: str) -> str:
    """安全移动文件，处理冲突"""
    dst = resolve_conflict(dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    os.rename(src, dst)
    return dst


def validate_path(requested_path: str, allowed_roots: list[str]) -> str:
    """确保路径在允许的目录范围内"""
    real_path = os.path.realpath(requested_path)
    for root in allowed_roots:
        if real_path.startswith(os.path.realpath(root)):
            return real_path
    raise ValueError("路径不在允许的目录中")
