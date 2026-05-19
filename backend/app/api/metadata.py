from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.media import Media
from app.schemas.common import ApiResponse
from app.services.metadata_service import MetadataService
from app.services.ai_service import AIService
from app.core.exceptions import NotFoundException, ValidationException

router = APIRouter()


class GenerateRequest(BaseModel):
    media_ids: list[int]
    generate_nfo: bool = True
    generate_covers: bool = True


class WriteTagsRequest(BaseModel):
    media_ids: list[int]
    fields: list[str] = ["artist", "album", "genre", "comment"]


class AiAnalyzeRequest(BaseModel):
    media_ids: list[int]


@router.post("/metadata/generate")
async def generate_metadata(
    request: GenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """生成元数据文件（NFO 等）"""
    result = await db.execute(select(Media).where(Media.id.in_(request.media_ids)))
    medias = list(result.scalars().all())
    if not medias:
        raise NotFoundException("未找到指定的媒体文件")

    generated = 0
    for media in medias:
        if request.generate_nfo and media.media_type == "video":
            generated += 1

    return ApiResponse(data={"generated": generated, "total": len(medias)})


@router.post("/metadata/write-tags")
async def write_tags(
    request: WriteTagsRequest,
    db: AsyncSession = Depends(get_db),
):
    """将元数据标签写入音频文件"""
    result = await db.execute(select(Media).where(Media.id.in_(request.media_ids)))
    medias = list(result.scalars().all())
    if not medias:
        raise NotFoundException("未找到指定的媒体文件")

    service = MetadataService()
    success = 0
    failed = 0

    for media in medias:
        tags = {}
        if "artist" in request.fields and media.cv:
            tags["artist"] = media.cv
        if "album" in request.fields and media.title:
            tags["title"] = media.title
        if "genre" in request.fields:
            tags["genre"] = "ASMR"
        if "comment" in request.fields and media.rj_id:
            tags["comment"] = media.rj_id

        if tags:
            ok = await service.write_audio_tags(media.file_path, tags)
            if ok:
                success += 1
            else:
                failed += 1

    return ApiResponse(data={"success": success, "failed": failed, "total": len(medias)})


@router.post("/metadata/ai-analyze")
async def ai_analyze(
    request: AiAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """用 AI 分析媒体文件名，自动填充元数据"""
    ai = AIService()
    if not ai.enabled:
        raise ValidationException("AI 服务未启用，请在设置中配置 API 地址和密钥")

    result = await db.execute(select(Media).where(Media.id.in_(request.media_ids)))
    medias = list(result.scalars().all())
    if not medias:
        raise NotFoundException("未找到指定的媒体文件")

    updated = 0
    results = []

    for media in medias:
        try:
            info = await ai.analyze_media_title(media.file_name)
            if not info:
                results.append({"id": media.id, "status": "no_result"})
                continue

            changed = False
            if info.get("title") and not media.title:
                media.title = info["title"]
                changed = True
            if info.get("cv") and not media.cv:
                media.cv = info["cv"]
                changed = True
            if info.get("circle") and not media.circle:
                media.circle = info["circle"]
                changed = True
            if info.get("rj_id") and not media.rj_id:
                media.rj_id = info["rj_id"]
                changed = True
            if info.get("language") and not media.language:
                media.language = info["language"]
                changed = True

            if changed:
                updated += 1
                results.append({"id": media.id, "status": "updated", "info": info})
            else:
                results.append({"id": media.id, "status": "no_change"})
        except Exception as e:
            results.append({"id": media.id, "status": "error", "error": str(e)})

    await db.commit()
    return ApiResponse(data={"updated": updated, "total": len(medias), "results": results})
