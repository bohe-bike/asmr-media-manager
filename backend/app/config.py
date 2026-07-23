import json
from pathlib import Path
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR.parent / ".env"
RUNTIME_SETTINGS_FILE = BASE_DIR / "data" / "runtime_settings.json"


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
    return Settings(**_load_runtime_settings())


def reload_settings() -> Settings:
    """清除缓存并重新加载设置"""
    get_settings.cache_clear()
    return get_settings()


def _load_runtime_settings() -> dict:
    """读取由设置页保存的持久化覆盖项。"""
    if not RUNTIME_SETTINGS_FILE.exists():
        return {}

    try:
        data = json.loads(RUNTIME_SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


def save_runtime_settings(updates: dict) -> None:
    """将设置页的覆盖项保存到数据目录，兼容 Docker 的环境变量配置。"""
    settings = _load_runtime_settings()
    settings.update(updates)

    # 使用 Settings 本身验证合并后的内容，避免把无效配置持久化。
    Settings(**settings)

    RUNTIME_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = RUNTIME_SETTINGS_FILE.with_suffix(".tmp")
    temp_file.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp_file.replace(RUNTIME_SETTINGS_FILE)
