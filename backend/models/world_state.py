from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
from .base import Base


class WorldState(Base):
    __tablename__ = "world_states"

    id = Column(Integer, primary_key=True, index=True)
    current_day = Column(Integer, default=1)
    current_scene = Column(String(50), default="classroom")
    narrative_phase = Column(String(50), nullable=True)
    global_flags = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))