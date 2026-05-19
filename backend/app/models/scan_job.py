from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text

from app.database import Base


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_path = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    scan_type = Column(String(20), nullable=False, default="full")  # full / incremental
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    new_files = Column(Integer, default=0)
    error_files = Column(Integer, default=0)
    errors = Column(Text)  # JSON string
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
