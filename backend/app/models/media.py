from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, CheckConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(Text, nullable=False, unique=True)
    file_name = Column(Text, nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    media_type = Column(String(10), nullable=False, index=True)  # audio / video
    format = Column(String(20), nullable=False)
    duration = Column(Float)
    bitrate = Column(Integer)
    sample_rate = Column(Integer)
    channels = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    title = Column(Text)
    rj_id = Column(String(20), index=True)
    dl_id = Column(String(20))
    creator = Column(String(200), index=True)
    circle = Column(String(200))
    cv = Column(String(200), index=True)
    platform = Column(String(20))  # dlsite / patreon / youtube / other
    language = Column(String(10))  # ja / zh / en / other
    cover_path = Column(Text)
    nfo_path = Column(Text)
    status = Column(String(20), nullable=False, default="pending", index=True)
    plex_ready = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    scanned_at = Column(DateTime)

    tags = relationship("MediaTag", back_populates="media", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("media_type IN ('audio', 'video')", name="check_media_type"),
        CheckConstraint(
            "platform IN ('dlsite', 'patreon', 'youtube', 'other') OR platform IS NULL",
            name="check_platform",
        ),
        CheckConstraint(
            "language IN ('ja', 'zh', 'en', 'other') OR language IS NULL",
            name="check_language",
        ),
        CheckConstraint(
            "status IN ('pending', 'processed', 'renamed', 'error')",
            name="check_status",
        ),
    )
