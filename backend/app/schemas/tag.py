from datetime import datetime
from pydantic import BaseModel


class TagCreate(BaseModel):
    name: str
    category: str | None = None


class TagResponse(BaseModel):
    id: int
    name: str
    category: str | None = None
    source: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MediaTagRequest(BaseModel):
    tag_ids: list[int]
    source: str = "user"
