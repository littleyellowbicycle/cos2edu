from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000, description="消息内容")