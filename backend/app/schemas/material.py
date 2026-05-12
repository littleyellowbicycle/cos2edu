from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class MaterialBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="教材标题")
    description: Optional[str] = Field(None, max_length=1000, description="教材描述")
    content_type: str = Field(default="text", description="内容类型: text, url, file")
    content: Optional[str] = Field(None, max_length=100000, description="教材内容(文本)")
    content_url: Optional[str] = Field(None, max_length=500, description="教材内容(URL或文件路径)")


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    content_type: Optional[str] = Field(None, max_length=20)
    content: Optional[str] = Field(None, max_length=100000)
    content_url: Optional[str] = Field(None, max_length=500)


class MaterialResponse(MaterialBase):
    id: int = Field(..., ge=1, description="教材ID")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)