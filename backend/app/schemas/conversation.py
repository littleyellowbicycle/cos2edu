from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime

from .enums import TeachingMode
from .character import CharacterResponse
from .material import MaterialResponse
from .message import MessageResponse, MessageCreate


class ConversationBase(BaseModel):
    title: Optional[str] = Field(None, max_length=200, description="对话标题")
    character_id: int = Field(..., ge=1, description="角色ID")
    material_id: Optional[int] = Field(None, ge=1, description="教材ID")
    teaching_mode: str = Field(default="socratic", description="教学模式")

    @field_validator("teaching_mode")
    @classmethod
    def validate_teaching_mode(cls, v: str) -> str:
        valid_modes = [t.value for t in TeachingMode]
        if v and v.lower() not in valid_modes:
            raise ValueError(f"无效的教学模式。支持的模式: {', '.join(valid_modes)}")
        return v.lower()


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    material_id: Optional[int] = Field(None, ge=1)
    teaching_mode: Optional[str] = None

    @field_validator("teaching_mode")
    @classmethod
    def validate_teaching_mode(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_modes = [t.value for t in TeachingMode]
        if v.lower() not in valid_modes:
            raise ValueError(f"无效的教学模式。支持的模式: {', '.join(valid_modes)}")
        return v.lower()


class ConversationResponse(ConversationBase):
    id: int = Field(..., ge=1, description="对话ID")
    created_at: datetime
    updated_at: datetime
    character: Optional[CharacterResponse] = None
    material: Optional[MaterialResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationWithMessages(ConversationResponse):
    messages: List[MessageResponse] = []