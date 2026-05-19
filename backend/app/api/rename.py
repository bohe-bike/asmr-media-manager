from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.media import Media
from app.schemas.rename import (
    RenamePreviewRequest,
    RenamePreviewResponse,
    RenameExecuteRequest,
    RenameExecuteResponse,
    RollbackRequest,
    RollbackResponse,
)
from app.schemas.common import ApiResponse
from app.services.rename_service import RenameService
from app.core.exceptions import NotFoundException

router = APIRouter()


@router.post("/rename/preview", )
async def preview_rename(
    request: RenamePreviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """预览重命名操作"""
    result = await db.execute(
        select(Media).where(Media.id.in_(request.media_ids))
    )
    medias = list(result.scalars().all())
    if not medias:
        raise NotFoundException("未找到指定的媒体文件")

    service = RenameService(db)
    preview = await service.preview(medias, request.pattern)
    return ApiResponse(data=preview)


@router.post("/rename/execute", )
async def execute_rename(
    request: RenameExecuteRequest,
    db: AsyncSession = Depends(get_db),
):
    """执行重命名操作"""
    result = await db.execute(
        select(Media).where(Media.id.in_(request.media_ids))
    )
    medias = list(result.scalars().all())
    if not medias:
        raise NotFoundException("未找到指定的媒体文件")

    service = RenameService(db)
    response = await service.execute(medias, request.pattern, request.move_cover)
    return ApiResponse(data=response)


@router.post("/rename/rollback")
async def rollback_rename(
    request: RollbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """回滚重命名操作：将文件移回原路径"""
    import os
    import shutil

    result = await db.execute(select(Media).where(Media.id.in_(request.media_ids)))
    medias = list(result.scalars().all())
    if not medias:
        raise NotFoundException("未找到指定的媒体文件")

    success = 0
    failed = 0

    for media in medias:
        try:
            # Parse original path from file_name or error_message
            # Rollback moves the file back to the download directory
            current_path = media.file_path
            if not os.path.exists(current_path):
                failed += 1
                continue

            # Move back to download directory
            from app.config import get_settings
            settings = get_settings()
            original_path = os.path.join(settings.download_dir, media.file_name)

            if os.path.exists(original_path):
                # Add suffix to avoid conflict
                base, ext = os.path.splitext(original_path)
                counter = 2
                while os.path.exists(f"{base} ({counter}){ext}"):
                    counter += 1
                original_path = f"{base} ({counter}){ext}"

            shutil.move(current_path, original_path)
            media.file_path = original_path
            media.status = "pending"
            success += 1
        except Exception as e:
            failed += 1

    await db.commit()
    return ApiResponse(data=RollbackResponse(success=success, failed=failed))
