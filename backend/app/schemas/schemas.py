from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum


class TeachingMode(str, Enum):
    SOCRATIC = "socratic"
    EXPLANATION = "explanation"
    MIXED = "mixed"


class AvatarType(str, Enum):
    EMOJI = "emoji"
    IMAGE = "image"


class BackgroundType(str, Enum):
    COLOR = "color"
    IMAGE = "image"


class ProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DASHSCOPE = "dashscope"
    ZHIPU = "zhipu"
    DOUBAO = "doubao"
    WENXIN = "wenxin"
    HUNYUAN = "hunyuan"
    MOONSHOT = "moonshot"
    GEMINI = "gemini"
    MINIMAX = "minimax"
    CUSTOM = "custom"


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

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    role: str = Field(..., description="消息角色")
    content: str = Field(..., min_length=1, description="消息内容")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = ["user", "assistant", "system"]
        if v.lower() not in valid_roles:
            raise ValueError(f"无效的消息角色。支持的角色: {', '.join(valid_roles)}")
        return v.lower()


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int = Field(..., ge=1, description="消息ID")
    conversation_id: int = Field(..., ge=1, description="对话ID")
    created_at: datetime

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    messages: List[MessageResponse] = []


class ChatMessage(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000, description="消息内容")


class ModelConfigBase(BaseModel):
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
    id: int = Field(..., ge=1, description="配置ID")
    provider: str
    model_name: str
    base_url: Optional[str] = None
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True
