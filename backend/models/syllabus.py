from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Syllabus(Base):
    __tablename__ = "syllabuses"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    name = Column(String(200), nullable=False)
    total_days = Column(Integer, default=90)
    content = Column(JSON, nullable=False)
    generated_by = Column(String(20), default="llm")
    review_status = Column(String(20), default="pending")
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    material = relationship("Material")