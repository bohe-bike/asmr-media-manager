from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings, save_runtime_settings, reload_settings
from app.schemas.common import ApiResponse

router = APIRouter()


class SettingsResponse(BaseModel):
    download_dir: str
    library_dir: str
    watch_dirs: list[str]
    watch_enabled: bool
    watch_auto_organize: bool
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
    dlsite_enabled: bool
    dlsite_api_base: str
    dlsite_cache_ttl: int
    dlsite_rate_limit: float
    dlsite_timeout: float
    dlsite_proxy: str
    plex_url: str
    plex_token: str
    plex_auto_refresh: bool


class SettingsUpdate(BaseModel):
    download_dir: str | None = None
    library_dir: str | None = None
    watch_dirs: list[str] | None = None
    watch_enabled: bool | None = None
    watch_auto_organize: bool | None = None
    stable_seconds: int | None = None
    audio_rename_pattern: str | None = None
    video_rename_pattern: str | None = None
    ai_enabled: bool | None = None
    ai_api_url: str | None = None
    ai_api_key: str | None = None
    ai_model: str | None = None
    ocr_enabled: bool | None = None
    dlsite_enabled: bool | None = None
    dlsite_api_base: str | None = None
    dlsite_cache_ttl: int | None = None
    dlsite_rate_limit: float | None = None
    dlsite_timeout: float | None = None
    dlsite_proxy: str | None = None
    plex_url: str | None = None
    plex_token: str | None = None
    plex_auto_refresh: bool | None = None


def _build_response(settings) -> SettingsResponse:
    return SettingsResponse(
        download_dir=settings.download_dir,
        library_dir=settings.library_dir,
        watch_dirs=settings.watch_dirs,
        watch_enabled=settings.watch_enabled,
        watch_auto_organize=settings.watch_auto_organize,
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
        dlsite_enabled=settings.dlsite_enabled,
        dlsite_api_base=settings.dlsite_api_base,
        dlsite_cache_ttl=settings.dlsite_cache_ttl,
        dlsite_rate_limit=settings.dlsite_rate_limit,
        dlsite_timeout=settings.dlsite_timeout,
        dlsite_proxy=settings.dlsite_proxy,
        plex_url=settings.plex_url,
        plex_token=settings.plex_token,
        plex_auto_refresh=settings.plex_auto_refresh,
    )


@router.get("/settings")
async def get_current_settings():
    """获取当前设置"""
    settings = get_settings()
    return ApiResponse(data=_build_response(settings))


@router.patch("/settings")
async def update_settings(update: SettingsUpdate):
    """更新设置并持久化到数据目录。"""
    updates = update.model_dump(exclude_unset=True)
    if not updates:
        settings = get_settings()
        return ApiResponse(data=_build_response(settings))

    save_runtime_settings(updates)
    settings = reload_settings()
    from app.main import restart_watcher
    await restart_watcher()
    return ApiResponse(message="设置已保存", data=_build_response(settings))


@router.post("/settings/test-plex")
async def test_plex_connection():
    """测试 Plex 连接"""
    from app.services.plex_service import PlexService

    plex = PlexService()
    result = await plex.test_connection()
    if result.get("connected"):
        return ApiResponse(message=f"Plex 连接成功: {result['name']} (v{result['version']})", data=result)
    else:
        return ApiResponse(code=400, message=f"Plex 连接失败: {result.get('error', '未知错误')}", data=result)
