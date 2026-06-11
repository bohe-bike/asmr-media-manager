import os
from pathlib import Path
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR.parent / ".env"


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    debug: bool = True

    # Database
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'asmr_manager.db'}"

    # Directories
    download_dir: str = "/media/downloads"
    library_dir: str = "/media/library"
    watch_dirs: list[str] = []  # 额外监控目录列表

    # Scan
    scan_recursive: bool = True
    watch_enabled: bool = True
    watch_auto_organize: bool = True  # 监控到新文件后是否自动整理到 library
    stable_seconds: int = 10
    check_interval: int = 5

    # Server
    host: str = "0.0.0.0"
    port: int = 8080
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    # AI
    ai_enabled: bool = False
    ai_api_url: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ocr_enabled: bool = False

    # DLsite
    dlsite_enabled: bool = True
    dlsite_api_base: str = "https://www.dlsite.com/maniax/api"
    dlsite_cache_ttl: int = 1800
    dlsite_rate_limit: float = 1.0
    dlsite_timeout: float = 10.0
    dlsite_proxy: str = ""

    # Plex
    plex_url: str = ""
    plex_token: str = ""
    plex_auto_refresh: bool = True

    # Supported formats
    supported_audio_formats: list[str] = ["mp3", "flac", "wav", "m4a", "opus", "ogg"]
    supported_video_formats: list[str] = ["mp4", "mkv", "avi", "mov", "webm"]

    # Rename
    audio_rename_pattern: str = "[{cv}] {title} ({rj_id})"
    video_rename_pattern: str = "[{creator}] {title}"
    max_filename_length: int = 200

    # Cover
    cover_filenames: list[str] = ["cover.jpg", "folder.jpg", "front.jpg"]
    cover_max_size: int = 1000

    # Organize
    unclassified_dir: str = "未分类"

    # Logging
    log_level: str = "INFO"

    model_config = {"env_file": str(ENV_FILE), "env_file_encoding": "utf-8"}

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production", "false", "0", "no", "off"}:
                return False
            if normalized in {"debug", "dev", "development", "true", "1", "yes", "on"}:
                return True
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    """清除缓存并重新加载设置"""
    get_settings.cache_clear()
    return get_settings()


def save_settings_to_env(updates: dict) -> None:
    """将设置变更写入 .env 文件"""
    # 读取现有 .env 内容
    existing: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                existing[key.strip()] = value.strip()

    # 更新值
    for key, value in updates.items():
        env_key = key.upper()
        if isinstance(value, bool):
            existing[env_key] = "true" if value else "false"
        elif isinstance(value, list):
            import json
            existing[env_key] = json.dumps(value)
        else:
            existing[env_key] = str(value)

    # 写回 .env
    lines = [f"{k}={v}" for k, v in sorted(existing.items())]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
