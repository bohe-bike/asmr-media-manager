import logging
import os

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.media import Media
from app.models.tag import MediaTag
from app.schemas.media import MediaResponse, MediaListItem, MediaListResponse, MediaUpdate, TagInfo
from app.schemas.common import ApiResponse
from app.core.exceptions import NotFoundException, ValidationException
from app.services.cover_service import CoverService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/media/stats")
async def get_media_stats(db: AsyncSession = Depends(get_db)):
    """获取媒体统计数据"""
    from sqlalchemy import func as sqlfunc

    total = (await db.execute(select(sqlfunc.count(Media.id)))).scalar() or 0
    audio = (await db.execute(select(sqlfunc.count(Media.id)).where(Media.media_type == "audio"))).scalar() or 0
    video = (await db.execute(select(sqlfunc.count(Media.id)).where(Media.media_type == "video"))).scalar() or 0
    classified = (await db.execute(select(sqlfunc.count(Media.id)).where(Media.creator.isnot(None)))).scalar() or 0
    with_rj = (await db.execute(select(sqlfunc.count(Media.id)).where(Media.rj_id.isnot(None)))).scalar() or 0

    return ApiResponse(data={
        "total": total,
        "audio": audio,
        "video": video,
        "classified": classified,
        "with_rj": with_rj,
        "unclassified": total - classified,
    })


@router.get("/media", )
async def list_media(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    media_type: str | None = None,
    status: str | None = None,
    creator: str | None = None,
    cv: str | None = None,
    rj_id: str | None = None,
    tag: str | None = None,
    unclassified: bool | None = None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
):
    """获取媒体列表"""
    query = select(Media).options(selectinload(Media.tags).selectinload(MediaTag.tag))

    # Filters
    if media_type:
        query = query.where(Media.media_type == media_type)
    if status:
        query = query.where(Media.status == status)
    if creator:
        query = query.where(Media.creator.contains(creator))
    if cv:
        query = query.where(Media.cv.contains(cv))
    if rj_id:
        query = query.where(Media.rj_id.contains(rj_id))
    if unclassified:
        query = query.where(Media.creator.is_(None))
    if search:
        query = query.where(
            (Media.title.contains(search))
            | (Media.file_name.contains(search))
            | (Media.creator.contains(search))
            | (Media.cv.contains(search))
        )

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Sort
    sort_col = getattr(Media, sort_by, Media.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    medias = result.scalars().unique().all()

    items = []
    for m in medias:
        tags = [
            TagInfo(id=mt.tag.id, name=mt.tag.name, source=mt.source)
            for mt in m.tags
            if mt.tag
        ]
        items.append(
            MediaListItem(
                id=m.id,
                file_name=m.file_name,
                media_type=m.media_type,
                title=m.title,
                rj_id=m.rj_id,
                cv=m.cv,
                circle=m.circle,
                creator=m.creator,
                platform=m.platform,
                duration=m.duration,
                format=m.format,
                file_size=m.file_size,
                status=m.status,
                tags=tags,
                cover_url=f"/api/v1/media/{m.id}/cover" if m.cover_path else None,
                description=m.description,
                metadata_source=m.metadata_source,
                created_at=m.created_at,
            )
        )

    return ApiResponse(data=MediaListResponse(items=items, total=total, page=page, page_size=page_size))


@router.get("/media/{media_id}", )
async def get_media(media_id: int, db: AsyncSession = Depends(get_db)):
    """获取媒体详情"""
    result = await db.execute(
        select(Media)
        .options(selectinload(Media.tags).selectinload(MediaTag.tag))
        .where(Media.id == media_id)
    )
    media = result.scalar_one_or_none()
    if not media:
        raise NotFoundException(f"媒体 {media_id} 不存在")

    tags = [
        TagInfo(id=mt.tag.id, name=mt.tag.name, source=mt.source)
        for mt in media.tags
        if mt.tag
    ]

    return ApiResponse(data=MediaResponse(
        id=media.id,
        file_path=media.file_path,
        file_name=media.file_name,
        file_hash=media.file_hash,
        file_size=media.file_size,
        media_type=media.media_type,
        format=media.format,
        duration=media.duration,
        bitrate=media.bitrate,
        sample_rate=media.sample_rate,
        channels=media.channels,
        width=media.width,
        height=media.height,
        title=media.title,
        rj_id=media.rj_id,
        dl_id=media.dl_id,
        creator=media.creator,
        circle=media.circle,
        cv=media.cv,
        platform=media.platform,
        language=media.language,
        cover_path=media.cover_path,
        status=media.status,
        plex_ready=media.plex_ready,
        error_message=media.error_message,
        tags=tags,
        cover_url=f"/api/v1/media/{media.id}/cover" if media.cover_path else None,
        description=media.description,
        metadata_source=media.metadata_source,
        created_at=media.created_at,
        updated_at=media.updated_at,
        scanned_at=media.scanned_at,
    ))


@router.patch("/media/{media_id}", )
async def update_media(
    media_id: int,
    update: MediaUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新媒体元数据"""
    result = await db.execute(
        select(Media)
        .options(selectinload(Media.tags).selectinload(MediaTag.tag))
        .where(Media.id == media_id)
    )
    media = result.scalar_one_or_none()
    if not media:
        raise NotFoundException(f"媒体 {media_id} 不存在")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(media, key, value)

    await db.commit()
    await db.refresh(media)

    tags = [
        TagInfo(id=mt.tag.id, name=mt.tag.name, source=mt.source)
        for mt in media.tags
        if mt.tag
    ]

    return ApiResponse(data=MediaResponse(
        id=media.id,
        file_path=media.file_path,
        file_name=media.file_name,
        file_hash=media.file_hash,
        file_size=media.file_size,
        media_type=media.media_type,
        format=media.format,
        duration=media.duration,
        bitrate=media.bitrate,
        sample_rate=media.sample_rate,
        channels=media.channels,
        width=media.width,
        height=media.height,
        title=media.title,
        rj_id=media.rj_id,
        dl_id=media.dl_id,
        creator=media.creator,
        circle=media.circle,
        cv=media.cv,
        platform=media.platform,
        language=media.language,
        cover_path=media.cover_path,
        status=media.status,
        plex_ready=media.plex_ready,
        error_message=media.error_message,
        tags=tags,
        cover_url=f"/api/v1/media/{media.id}/cover" if media.cover_path else None,
        description=media.description,
        metadata_source=media.metadata_source,
        created_at=media.created_at,
        updated_at=media.updated_at,
        scanned_at=media.scanned_at,
    ))


@router.get("/media/{media_id}/cover")
async def get_media_cover(media_id: int, db: AsyncSession = Depends(get_db)):
    """获取媒体封面图片"""
    result = await db.execute(select(Media).where(Media.id == media_id))
    media = result.scalar_one_or_none()
    if not media:
        raise NotFoundException(f"媒体 {media_id} 不存在")

    cover_service = CoverService()
    cover_path = media.cover_path

    if not cover_path or not os.path.exists(cover_path):
        cover_path = await cover_service.find_local_cover(media.file_path)
        if cover_path:
            media.cover_path = cover_path
            await db.commit()

    if not cover_path or not os.path.exists(cover_path):
        raise NotFoundException("封面不存在")

    return FileResponse(cover_path)


class OrganizePreviewRequest(BaseModel):
    media_ids: list[int]


class OrganizeExecuteRequest(BaseModel):
    media_ids: list[int]


@router.post("/media/organize/preview")
async def preview_organize(
    request: OrganizePreviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """预览整理操作：显示每个文件的目标路径，不实际移动"""
    from app.services.organize_service import OrganizeService
    from app.config import get_settings

    result = await db.execute(select(Media).where(Media.id.in_(request.media_ids)))
    medias = list(result.scalars().all())
    if not medias:
        raise NotFoundException("未找到指定的媒体文件")

    settings = get_settings()
    service = OrganizeService(settings.library_dir)

    items = []
    for media in medias:
        preview = service.preview(media)
        preview["media_id"] = media.id
        preview["file_name"] = media.file_name
        items.append(preview)

    return ApiResponse(data={"items": items, "total": len(items)})


@router.post("/media/organize/execute")
async def execute_organize(
    request: OrganizeExecuteRequest,
    db: AsyncSession = Depends(get_db),
):
    """执行整理操作：将文件移动到 library 目录并写入元数据"""
    from app.services.organize_service import OrganizeService
    from app.services.scanner import ScannerService
    from app.config import get_settings

    result = await db.execute(select(Media).where(Media.id.in_(request.media_ids)))
    medias = list(result.scalars().all())
    if not medias:
        raise NotFoundException("未找到指定的媒体文件")

    settings = get_settings()
    organize_service = OrganizeService(settings.library_dir)
    scanner = ScannerService(db)

    success = 0
    failed = 0
    results = []

    for media in medias:
        try:
            new_path = organize_service.move_to_library(media)
            media.file_path = new_path
            media.file_name = os.path.basename(new_path)
            media.status = "processed"
            await db.commit()

            # 后处理：写标签、下载封面
            try:
                await scanner._post_process(media)
            except Exception as e:
                logger.warning(f"Post-process failed for {media.id}: {e}")

            success += 1
            results.append({"media_id": media.id, "status": "success", "new_path": new_path})
        except Exception as e:
            logger.error(f"Organize failed for media {media.id}: {e}")
            failed += 1
            results.append({"media_id": media.id, "status": "failed", "error": str(e)})

    return ApiResponse(data={"success": success, "failed": failed, "results": results})


@router.post("/media/reorganize")
async def reorganize_files(
    request: OrganizeExecuteRequest,
    db: AsyncSession = Depends(get_db),
):
    """重新整理文件到新的目录结构（作者/[RJ号] 标题/文件）。

    适用于旧的平铺结构迁移到新的三级结构。
    """
    from app.services.organize_service import OrganizeService
    from app.services.scanner import ScannerService
    from app.config import get_settings

    result = await db.execute(select(Media).where(Media.id.in_(request.media_ids)))
    medias = list(result.scalars().all())
    if not medias:
        raise NotFoundException("未找到指定的媒体文件")

    settings = get_settings()
    organize_service = OrganizeService(settings.library_dir)
    scanner = ScannerService(db)

    success = 0
    failed = 0
    skipped = 0
    results = []

    for media in medias:
        try:
            # 检查是否已经在正确的目录结构中
            preview = organize_service.preview(media)
            if preview["new_path"] == media.file_path:
                skipped += 1
                results.append({"media_id": media.id, "status": "skipped", "reason": "已在正确目录"})
                continue

            # 如果文件不在预期位置（可能已经被移动过），跳过
            if not os.path.exists(media.file_path):
                # 尝试在 library 目录中查找
                possible_path = organize_service.preview(media)["new_path"]
                if os.path.exists(possible_path):
                    media.file_path = possible_path
                    skipped += 1
                    results.append({"media_id": media.id, "status": "skipped", "reason": "文件已在新位置"})
                    continue
                failed += 1
                results.append({"media_id": media.id, "status": "failed", "error": "文件不存在"})
                continue

            new_path = organize_service.move_to_library(media)
            media.file_path = new_path
            media.file_name = os.path.basename(new_path)
            await db.commit()

            # 重新写入标签
            try:
                await scanner._post_process(media)
            except Exception as e:
                logger.warning(f"Post-process failed for {media.id}: {e}")

            success += 1
            results.append({"media_id": media.id, "status": "success", "new_path": new_path})
        except Exception as e:
            logger.error(f"Reorganize failed for media {media.id}: {e}")
            failed += 1
            results.append({"media_id": media.id, "status": "failed", "error": str(e)})

    return ApiResponse(data={"success": success, "skipped": skipped, "failed": failed, "results": results})
