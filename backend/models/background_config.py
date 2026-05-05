from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from .base import Base


class BackgroundConfig(Base):
    __tablename__ = "background_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    background_type = Column(String(20), default="color")
    background_value = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
