from datetime import datetime
from pydantic import BaseModel


class AuthorRuleCreate(BaseModel):
    keyword: str
    match_type: str = "contains"
    match_target: str = "filename"
    creator: str | None = None
    circle: str | None = None
    cv: str | None = None
    priority: int = 0


class AuthorRuleUpdate(BaseModel):
    keyword: str | None = None
    match_type: str | None = None
    match_target: str | None = None
    creator: str | None = None
    circle: str | None = None
    cv: str | None = None
    priority: int | None = None
    enabled: bool | None = None


class AuthorRuleResponse(BaseModel):
    id: int
    keyword: str
    match_type: str
    match_target: str
    creator: str | None = None
    circle: str | None = None
    cv: str | None = None
    priority: int
    enabled: bool
    hit_count: int
    last_hit_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AuthorRuleListResponse(BaseModel):
    items: list[AuthorRuleResponse]
    total: int
    page: int
    page_size: int


class BatchAuthorRuleCreate(BaseModel):
    rules: list[AuthorRuleCreate]


class ScanTestResponse(BaseModel):
    total_media: int
    matched_media: int
    samples: list[dict]


class ApplyRequest(BaseModel):
    rule_ids: list[int] | None = None
    overwrite: bool = False


class ApplyResponse(BaseModel):
    total_checked: int
    newly_classified: int
    skipped: int
    overwritten: int
