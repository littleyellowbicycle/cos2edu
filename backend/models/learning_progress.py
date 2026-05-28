from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from .base import Base


class LearningProgress(Base):
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_point_id = Column(String(100), nullable=False, index=True)
    status = Column(String(20), default="locked")
    mastery_level = Column(Float, default=0.0)
    attempts = Column(Integer, default=0)
    last_reviewed_at = Column(DateTime, nullable=True)
    weak_areas = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))