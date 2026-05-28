from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    id = Column(Integer, primary_key=True, index=True)
    syllabus_id = Column(Integer, ForeignKey("syllabuses.id"), nullable=True)
    point_id = Column(String(100), nullable=False, index=True)
    module_name = Column(String(200), nullable=True)
    point_name = Column(String(200), nullable=False)
    difficulty = Column(Integer, default=1)
    key_concepts = Column(JSON, default=list)
    teaching_hints = Column(JSON, nullable=True)
    suggested_questions = Column(JSON, nullable=True)
    exercises = Column(JSON, nullable=True)
    prerequisites = Column(JSON, default=list)
    sort_order = Column(Integer, default=0)

    syllabus = relationship("Syllabus")