from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, CheckConstraint

from app.database import Base


class AuthorRule(Base):
    __tablename__ = "author_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(Text, nullable=False, index=True)
    match_type = Column(String(20), nullable=False, default="contains")
    match_target = Column(String(30), nullable=False, default="filename")
    creator = Column(String(200), index=True)
    circle = Column(String(200), index=True)
    cv = Column(String(200))
    priority = Column(Integer, nullable=False, default=0, index=True)
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    hit_count = Column(Integer, nullable=False, default=0)
    last_hit_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "match_type IN ('contains', 'exact', 'regex', 'prefix', 'suffix')",
            name="check_match_type",
        ),
        CheckConstraint(
            "match_target IN ('filename', 'metadata_artist', 'metadata_album', 'directory', 'all')",
            name="check_match_target",
        ),
    )
