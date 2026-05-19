from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings, save_settings_to_env, reload_settings
from app.schemas.common import ApiResponse

router = APIRouter()


class SettingsResponse(BaseModel):
    download_dir: str
    library_dir: str
    watch_enabled: bool
    stable_seconds: int
    audio_rename_pattern: str
    video_rename_pattern: str
    supported_audio_formats: list[str]
    supported_video_formats: list[str]
    ai_enabled: bool
    ai_api_url: str
    ai_api_key: str
    ai_model: str
    ocr_enabled: bool
    cover_filenames: list[str]
    unclassified_dir: str


class SettingsUpdate(BaseModel):
    download_dir: str | None = None
    library_dir: str | None = None
    watch_enabled: bool | None = None
    stable_seconds: int | None = None
    audio_rename_pattern: str | None = None
    video_rename_pattern: str | None = None
    ai_enabled: bool | None = None
    ai_api_url: str | None = None
    ai_api_key: str | None = None
    ai_model: str | None = None
    ocr_enabled: bool | None = None


def _build_response(settings) -> SettingsResponse:
    return SettingsResponse(
        download_dir=settings.download_dir,
        library_dir=settings.library_dir,
        watch_enabled=settings.watch_enabled,
        stable_seconds=settings.stable_seconds,
        audio_rename_pattern=settings.audio_rename_pattern,
        video_rename_pattern=settings.video_rename_pattern,
        supported_audio_formats=settings.supported_audio_formats,
        supported_video_formats=settings.supported_video_formats,
        ai_enabled=settings.ai_enabled,
        ai_api_url=settings.ai_api_url,
        ai_api_key=settings.ai_api_key,
        ai_model=settings.ai_model,
        ocr_enabled=settings.ocr_enabled,
        cover_filenames=settings.cover_filenames,
        unclassified_dir=settings.unclassified_dir,
    )


@router.get("/settings")
async def get_current_settings():
    """获取当前设置"""
    settings = get_settings()
    return ApiResponse(data=_build_response(settings))


@router.patch("/settings")
async def update_settings(update: SettingsUpdate):
    """更新设置并持久化到 .env 文件"""
    updates = update.model_dump(exclude_unset=True)
    if not updates:
        settings = get_settings()
        return ApiResponse(data=_build_response(settings))

    save_settings_to_env(updates)
    settings = reload_settings()
    return ApiResponse(message="设置已保存", data=_build_response(settings))
