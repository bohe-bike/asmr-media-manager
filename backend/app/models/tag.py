from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(20))  # type / mood / content / technical / custom
    source = Column(String(20))  # filename / ai / user / dlsite
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    media_tags = relationship("MediaTag", back_populates="tag", cascade="all, delete-orphan")


class MediaTag(Base):
    __tablename__ = "media_tags"

    media_id = Column(Integer, ForeignKey("media.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    confidence = Column(Float, default=1.0)
    source = Column(String(20))  # filename / ai / user / dlsite

    media = relationship("Media", back_populates="tags")
    tag = relationship("Tag", back_populates="media_tags")
