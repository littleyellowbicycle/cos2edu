from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class CharacterState(Base):
    __tablename__ = "character_states"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), unique=True)
    current_mood = Column(Float, default=0.7)
    trust_level = Column(Float, default=0.5)
    relationship_tags = Column(JSON, default=list)
    last_interaction_at = Column(DateTime, nullable=True)

    character = relationship("Character")