from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from .base import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    content_type = Column(String(20), default="text")
    content_url = Column(String(500), nullable=True)
    file_path = Column(String(255), nullable=True)
    status = Column(String(20), default="parsing")
    error_code = Column(String(50), nullable=True)
    review_status = Column(String(20), nullable=True)
    source_syllabus_id = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    char_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    conversations = relationship("Conversation", back_populates="material")