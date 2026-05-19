from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag, MediaTag
from app.models.media import Media


class TagService:
    """标签管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_tags(self, category: str | None = None, search: str | None = None) -> list[Tag]:
        query = select(Tag)
        if category:
            query = query.where(Tag.category == category)
        if search:
            query = query.where(Tag.name.contains(search))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_tag(self, name: str, category: str | None = None, source: str = "user") -> Tag:
        tag = Tag(name=name, category=category, source=source)
        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def add_tags_to_media(
        self, media_id: int, tag_ids: list[int], source: str = "user"
    ) -> None:
        for tag_id in tag_ids:
            # Check if already exists
            existing = await self.db.execute(
                select(MediaTag).where(
                    MediaTag.media_id == media_id,
                    MediaTag.tag_id == tag_id,
                )
            )
            if existing.scalar_one_or_none() is None:
                mt = MediaTag(media_id=media_id, tag_id=tag_id, source=source)
                self.db.add(mt)
        await self.db.commit()

    async def remove_tag_from_media(self, media_id: int, tag_id: int) -> None:
        result = await self.db.execute(
            select(MediaTag).where(
                MediaTag.media_id == media_id,
                MediaTag.tag_id == tag_id,
            )
        )
        mt = result.scalar_one_or_none()
        if mt:
            await self.db.delete(mt)
            await self.db.commit()

    async def get_or_create_tag(self, name: str, category: str | None = None) -> Tag:
        result = await self.db.execute(select(Tag).where(Tag.name == name))
        tag = result.scalar_one_or_none()
        if tag is None:
            tag = await self.create_tag(name, category)
        return tag
