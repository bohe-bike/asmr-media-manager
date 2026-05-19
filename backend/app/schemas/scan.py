from datetime import datetime
from pydantic import BaseModel


class ScanRequest(BaseModel):
    path: str
    scan_type: str = "full"
    recursive: bool = True


class ScanJobResponse(BaseModel):
    id: int
    scan_path: str
    status: str
    scan_type: str
    total_files: int = 0
    processed_files: int = 0
    new_files: int = 0
    error_files: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    progress_percent: float = 0.0

    model_config = {"from_attributes": True}
