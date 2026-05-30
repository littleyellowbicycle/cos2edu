from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import datetime


class ModelConfigBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider: str = Field(..., min_length=1, description="模型提供商")
    model_name: str = Field(..., min_length=1, max_length=100, description="模型名称")
    api_key: Optional[str] = Field(None, max_length=500, description="API密钥")
    base_url: Optional[str] = Field(None, max_length=500, description="API基地址")
    group_id: Optional[str] = Field(None, max_length=100, description="Group ID (MiniMax等需要)")
    is_default: bool = Field(default=False, description="是否为默认配置")

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v:
            v = v.strip().lower()
        if not v:
            raise ValueError("模型提供商不能为空")
        if len(v) > 50:
            raise ValueError("模型提供商名称太长（最多50个字符）")
        return v

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("base_url必须以http://或https://开头")
        if v.endswith("/"):
            v = v.rstrip("/")
        return v


class ModelConfigCreate(ModelConfigBase):
    pass


class ModelConfigUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider: Optional[str] = Field(None, min_length=1)
    model_name: Optional[str] = Field(None, min_length=1, max_length=100)
    api_key: Optional[str] = Field(None, max_length=500)
    base_url: Optional[str] = Field(None, max_length=500)
    group_id: Optional[str] = Field(None, max_length=100)
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().lower()
        if not v:
            raise ValueError("模型提供商不能为空")
        if len(v) > 50:
            raise ValueError("模型提供商名称太长（最多50个字符）")
        return v

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("base_url必须以http://或https://开头")
        if v.endswith("/"):
            v = v.rstrip("/")
        return v


class ModelConfigResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int = Field(..., ge=1, description="配置ID")
    provider: str
    model_name: str
    base_url: Optional[str] = None
    has_api_key: bool = Field(default=False, description="是否已配置 API Key")
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def resolve_has_api_key(cls, data: Any) -> Any:
        if isinstance(data, dict):
            api_key = data.get("api_key")
        else:
            api_key = getattr(data, "api_key", None)
        if isinstance(data, dict):
            data["has_api_key"] = bool(api_key)
        else:
            data.has_api_key = bool(api_key)
        return data