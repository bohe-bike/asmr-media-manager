from datetime import datetime
from pydantic import BaseModel


class TagInfo(BaseModel):
    id: int
    name: str
    source: str | None = None

    model_config = {"from_attributes": True}


class MediaResponse(BaseModel):
    id: int
    file_path: str
    file_name: str
    file_hash: str
    file_size: int
    media_type: str
    format: str
    duration: float | None = None
    bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    width: int | None = None
    height: int | None = None
    title: str | None = None
    rj_id: str | None = None
    dl_id: str | None = None
    creator: str | None = None
    circle: str | None = None
    cv: str | None = None
    platform: str | None = None
    language: str | None = None
    cover_path: str | None = None
    cover_url: str | None = None
    description: str | None = None
    metadata_source: str | None = None
    status: str
    plex_ready: bool
    error_message: str | None = None
    tags: list[TagInfo] = []
    created_at: datetime
    updated_at: datetime
    scanned_at: datetime | None = None

    model_config = {"from_attributes": True}


class MediaListItem(BaseModel):
    id: int
    file_name: str
    media_type: str
    title: str | None = None
    rj_id: str | None = None
    cv: str | None = None
    circle: str | None = None
    creator: str | None = None
    platform: str | None = None
    duration: float | None = None
    format: str
    file_size: int
    status: str
    tags: list[TagInfo] = []
    cover_url: str | None = None
    description: str | None = None
    metadata_source: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MediaListResponse(BaseModel):
    items: list[MediaListItem]
    total: int
    page: int
    page_size: int


class MediaUpdate(BaseModel):
    title: str | None = None
    creator: str | None = None
    circle: str | None = None
    cv: str | None = None
    rj_id: str | None = None
    platform: str | None = None
    language: str | None = None
