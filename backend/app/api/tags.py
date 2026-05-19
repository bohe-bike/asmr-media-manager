from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tag import Tag, MediaTag
from app.models.media import Media
from app.schemas.tag import TagCreate, TagResponse, MediaTagRequest
from app.schemas.common import ApiResponse
from app.core.exceptions import NotFoundException

router = APIRouter()


@router.get("/tags", )
async def list_tags(
    category: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """获取所有标签"""
    query = select(Tag)
    if category:
        query = query.where(Tag.category == category)
    if search:
        query = query.where(Tag.name.contains(search))
    result = await db.execute(query)
    tags = result.scalars().all()
    return ApiResponse(data=[TagResponse.model_validate(t) for t in tags])


@router.post("/tags", )
async def create_tag(request: TagCreate, db: AsyncSession = Depends(get_db)):
    """创建新标签"""
    tag = Tag(name=request.name, category=request.category, source="user")
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return ApiResponse(data=TagResponse.model_validate(tag))


@router.post("/media/{media_id}/tags")
async def add_tags_to_media(
    media_id: int,
    request: MediaTagRequest,
    db: AsyncSession = Depends(get_db),
):
    """为媒体添加标签"""
    # Verify media exists
    result = await db.execute(select(Media).where(Media.id == media_id))
    if not result.scalar_one_or_none():
        raise NotFoundException(f"媒体 {media_id} 不存在")

    for tag_id in request.tag_ids:
        # Check if already exists
        existing = await db.execute(
            select(MediaTag).where(
                MediaTag.media_id == media_id,
                MediaTag.tag_id == tag_id,
            )
        )
        if existing.scalar_one_or_none() is None:
            mt = MediaTag(media_id=media_id, tag_id=tag_id, source=request.source)
            db.add(mt)

    await db.commit()
    return ApiResponse(message="标签已添加")


@router.delete("/media/{media_id}/tags/{tag_id}")
async def remove_tag_from_media(
    media_id: int,
    tag_id: int,
    db: AsyncSession = Depends(get_db),
):
    """移除媒体标签"""
    result = await db.execute(
        select(MediaTag).where(
            MediaTag.media_id == media_id,
            MediaTag.tag_id == tag_id,
        )
    )
    mt = result.scalar_one_or_none()
    if not mt:
        raise NotFoundException("标签关联不存在")

    await db.delete(mt)
    await db.commit()
    return ApiResponse(message="标签已移除")
