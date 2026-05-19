from pydantic import BaseModel


class RenamePreviewRequest(BaseModel):
    media_ids: list[int]
    pattern: str | None = None


class RenamePreviewItem(BaseModel):
    media_id: int
    old_path: str
    new_path: str
    new_dir: str | None = None
    conflict: bool = False


class RenamePreviewResponse(BaseModel):
    items: list[RenamePreviewItem]
    conflicts: list[dict] = []
    total: int


class RenameExecuteRequest(BaseModel):
    media_ids: list[int]
    pattern: str | None = None
    create_dirs: bool = True
    move_cover: bool = True


class RenameResultItem(BaseModel):
    media_id: int
    old_path: str
    new_path: str
    status: str


class RenameExecuteResponse(BaseModel):
    success: int
    failed: int
    results: list[RenameResultItem]


class RollbackRequest(BaseModel):
    media_ids: list[int]


class RollbackResponse(BaseModel):
    success: int
    failed: int
