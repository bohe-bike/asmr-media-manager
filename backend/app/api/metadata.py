from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import os
import xml.etree.ElementTree as ET

from app.database import get_db
from app.models.media import Media
from app.schemas.common import ApiResponse
from app.services.metadata_service import MetadataService
from app.services.ai_service import AIService
from app.services.cover_service import CoverService
from app.services.dlsite_service import DlsiteService
from app.services.tag_service import TagService
from app.core.exceptions import NotFoundException, ValidationException

router = APIRouter()


class GenerateRequest(BaseModel):
    media_ids: list[int]
    generate_nfo: bool = True
    generate_covers: bool = True


class WriteTagsRequest(BaseModel):
    media_ids: list[int]
    fields: list[str] = ["title", "album", "artist", "album_artist", "genre", "comment"]


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
    failed = 0
    cover_service = CoverService()
    for media in medias:
        try:
            changed = False
            if request.generate_nfo:
                media.nfo_path = _write_nfo(media)
                changed = True
            if request.generate_covers:
                cover_path = await cover_service.find_local_cover(media.file_path)
                if cover_path:
                    media.cover_path = cover_path
                    changed = True
            if changed:
                generated += 1
        except Exception:
            failed += 1

    await db.commit()
    return ApiResponse(data={"generated": generated, "failed": failed, "total": len(medias)})


def _write_nfo(media: Media) -> str:
    """在媒体文件旁生成基础 NFO，供本地媒体库读取。"""
    media_dir = os.path.dirname(media.file_path)
    base_name = os.path.splitext(os.path.basename(media.file_path))[0]
    nfo_path = os.path.join(media_dir, f"{base_name}.nfo")

    root = ET.Element("movie" if media.media_type == "video" else "album")
    fields = {
        "title": media.title or os.path.splitext(media.file_name)[0],
        "originaltitle": media.file_name,
        "studio": media.circle,
        "artist": media.creator or media.cv,
        "genre": "ASMR",
        "tag": media.rj_id,
        "plot": media.description,
    }
    for key, value in fields.items():
        if value:
            child = ET.SubElement(root, key)
            child.text = str(value)

    if media.cv:
        actor = ET.SubElement(root, "actor")
        name = ET.SubElement(actor, "name")
        name.text = media.cv

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write(nfo_path, encoding="utf-8", xml_declaration=True)
    return nfo_path


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
    cover_service = CoverService()
    success = 0
    failed = 0

    for media in medias:
        tags = {}
        if "title" in request.fields and media.title:
            tags["title"] = media.title
        if "album" in request.fields and media.title:
            tags["album"] = f"[{media.rj_id}] {media.title}" if media.rj_id else media.title
        if "artist" in request.fields and (media.creator or media.cv):
            tags["artist"] = media.creator or media.cv
        if "album_artist" in request.fields and media.circle:
            tags["album_artist"] = media.circle
        if "genre" in request.fields:
            tags["genre"] = "ASMR"
        if "comment" in request.fields and media.rj_id:
            tags["comment"] = media.rj_id

        if tags:
            cover_path = media.cover_path
            if not cover_path or not os.path.exists(cover_path):
                cover_path = await cover_service.find_local_cover(media.file_path)
            ok = await service.write_audio_tags(media.file_path, tags, cover_path=cover_path)
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


class DlsiteFetchRequest(BaseModel):
    media_ids: list[int]
    overwrite: bool = False


@router.post("/metadata/fetch-dlsite")
async def fetch_dlsite_metadata(
    request: DlsiteFetchRequest,
    db: AsyncSession = Depends(get_db),
):
    """根据 RJ/DL 号从 DLsite 获取元数据并补全媒体信息（并发批量请求）"""
    dlsite = DlsiteService()
    if not dlsite.enabled:
        raise ValidationException("DLsite 服务未启用，请在设置中开启")

    result = await db.execute(select(Media).where(Media.id.in_(request.media_ids)))
    medias = list(result.scalars().all())
    if not medias:
        raise NotFoundException("未找到指定的媒体文件")

    tag_service = TagService(db)
    updated = 0
    skipped = 0
    failed = 0
    results = []

    # 收集需要查询的 work_id
    media_by_work_id: dict[str, list] = {}
    for media in medias:
        work_id = (media.rj_id or media.dl_id or "").upper().strip()
        if not work_id:
            skipped += 1
            results.append({"id": media.id, "status": "no_rj_id"})
            continue
        if work_id not in media_by_work_id:
            media_by_work_id[work_id] = []
        media_by_work_id[work_id].append(media)

    # 批量并发获取 DLsite 数据
    work_ids = list(media_by_work_id.keys())
    dlsite_results = await dlsite.fetch_batch(work_ids)

    # 应用结果到每个 media
    for work_id, data in dlsite_results.items():
        medias_for_id = media_by_work_id.get(work_id, [])
        for media in medias_for_id:
            try:
                if not data:
                    failed += 1
                    results.append({"id": media.id, "status": "fetch_failed"})
                    continue

                changed = False
                if data.get("title") and (not media.title or request.overwrite):
                    media.title = data["title"]
                    changed = True
                if data.get("creator") and (not media.creator or request.overwrite):
                    media.creator = data["creator"]
                    changed = True
                if data.get("circle") and (not media.circle or request.overwrite):
                    media.circle = data["circle"]
                    changed = True
                if data.get("cv") and (not media.cv or request.overwrite):
                    media.cv = data["cv"]
                    changed = True
                if data.get("language") and (not media.language or request.overwrite):
                    media.language = data["language"]
                    changed = True
                if data.get("description") and (not media.description or request.overwrite):
                    media.description = data["description"]
                    changed = True
                if data.get("cover_url") and (not media.cover_url or request.overwrite):
                    media.cover_url = data["cover_url"]
                    changed = True

                # 自动添加 DLsite 返回的标签
                if data.get("tags"):
                    for tag_name in data["tags"]:
                        tag = await tag_service.get_or_create_tag(tag_name, category="dlsite")
                        await tag_service.add_tags_to_media(media.id, [tag.id], source="dlsite")

                if changed:
                    media.metadata_source = "dlsite"
                    updated += 1
                    results.append({"id": media.id, "status": "updated", "work_id": work_id})
                else:
                    results.append({"id": media.id, "status": "no_change"})

            except Exception as e:
                logger.error(f"DLsite 补全失败 media {media.id} ({work_id}): {e}")
                failed += 1
                results.append({"id": media.id, "status": "error", "error": str(e)})

    await db.commit()
    return ApiResponse(data={
        "updated": updated,
        "skipped": skipped,
        "failed": failed,
        "total": len(medias),
        "results": results,
    })
