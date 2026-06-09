from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime


class MessageBase(BaseModel):
    role: str = Field(..., description="消息角色")
    content: str = Field(..., min_length=1, description="消息内容")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = ["user", "assistant", "system", "tool", "function"]
        if v.lower() not in valid_roles:
            raise ValueError(f"无效的消息角色。支持的角色: {', '.join(valid_roles)}")
        return v.lower()


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int = Field(..., ge=1, description="消息ID")
    conversation_id: int = Field(..., ge=1, description="对话ID")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)