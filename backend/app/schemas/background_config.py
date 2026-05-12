from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime

from .enums import BackgroundType


class BackgroundConfigBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="背景名称")
    background_type: str = Field(default="color", description="背景类型")
    background_value: str = Field(..., min_length=1, max_length=500, description="背景值")

    @field_validator("background_type")
    @classmethod
    def validate_background_type(cls, v: str) -> str:
        valid_types = [t.value for t in BackgroundType]
        if v and v.lower() not in valid_types:
            raise ValueError(f"无效的背景类型。支持的类型: {', '.join(valid_types)}")
        return v.lower()


class BackgroundConfigCreate(BackgroundConfigBase):
    is_default: bool = Field(default=False, description="是否为默认背景")


class BackgroundConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    background_type: Optional[str] = None
    background_value: Optional[str] = Field(None, min_length=1, max_length=500)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

    @field_validator("background_type")
    @classmethod
    def validate_background_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_types = [t.value for t in BackgroundType]
        if v.lower() not in valid_types:
            raise ValueError(f"无效的背景类型。支持的类型: {', '.join(valid_types)}")
        return v.lower()


class BackgroundConfigResponse(BackgroundConfigBase):
    id: int = Field(..., ge=1, description="背景配置ID")
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)