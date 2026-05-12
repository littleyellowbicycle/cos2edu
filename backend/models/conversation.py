from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=True)
    character_id = Column(Integer, ForeignKey("characters.id"))
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    teaching_mode = Column(String(50), default="socratic")
    
    summary = Column(Text, nullable=True)
    summary_covered_message_count = Column(Integer, default=0)
    summary_created_at = Column(DateTime, nullable=True)
    summary_updated_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    character = relationship("Character", back_populates="conversations")
    material = relationship("Material", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")
