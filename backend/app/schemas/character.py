from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime

from .enums import AvatarType


class CharacterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="角色名称")
    description: Optional[str] = Field(None, max_length=500, description="角色描述")
    personality: str = Field(default="善良且乐于助人", max_length=2000, description="角色性格设定")
    background: Optional[str] = Field(None, max_length=2000, description="角色背景故事")
    avatar: Optional[str] = Field(None, max_length=500, description="头像路径或表情")
    avatar_type: str = Field(default="emoji", description="头像类型")

    @field_validator("avatar_type")
    @classmethod
    def validate_avatar_type(cls, v: str) -> str:
        valid_types = [t.value for t in AvatarType]
        if v and v.lower() not in valid_types:
            raise ValueError(f"无效的头像类型。支持的类型: {', '.join(valid_types)}")
        return v.lower()


class CharacterCreate(CharacterBase):
    pass


class CharacterUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    personality: Optional[str] = Field(None, max_length=2000)
    background: Optional[str] = Field(None, max_length=2000)
    avatar: Optional[str] = Field(None, max_length=500)
    avatar_type: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("avatar_type")
    @classmethod
    def validate_avatar_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_types = [t.value for t in AvatarType]
        if v.lower() not in valid_types:
            raise ValueError(f"无效的头像类型。支持的类型: {', '.join(valid_types)}")
        return v.lower()


class CharacterResponse(CharacterBase):
    id: int = Field(..., ge=1, description="角色ID")
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)