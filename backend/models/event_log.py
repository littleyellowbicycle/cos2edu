from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from .base import Base


class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(30), nullable=False)
    event_id = Column(String(100), nullable=True)
    trigger_context = Column(JSON, nullable=True)
    resolved = Column(Boolean, default=False)
    resolution_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)