from typing import Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class WSMessage(BaseModel):
    type: str = Field(..., description="消息类型")
    payload: Optional[dict] = Field(default=None, description="消息负载")
    id: Optional[str] = Field(default=None, description="消息ID (用于请求-响应关联)")
    timestamp: Optional[float] = Field(default=None, description="Unix 时间戳")


class ChatSendMessage(BaseModel):
    type: str = "chat.send"
    payload: dict = Field(..., description="包含 content 字段")
    id: Optional[str] = None


class SceneSwitchMessage(BaseModel):
    type: str = "scene.switch"
    payload: dict = Field(..., description="包含 scene_id 字段")
    id: Optional[str] = None


class ActionChooseMessage(BaseModel):
    type: str = "action.choose"
    payload: dict = Field(..., description="包含 option_id 字段")
    id: Optional[str] = None


class StateSyncMessage(BaseModel):
    type: str = "state.sync"
    payload: Optional[dict] = None
    id: Optional[str] = None


class SyllabusConfirmMessage(BaseModel):
    type: str = "syllabus.confirm"
    payload: dict = Field(..., description="包含 material_id 字段")
    id: Optional[str] = None


class SyllabusRejectMessage(BaseModel):
    type: str = "syllabus.reject"
    payload: dict = Field(..., description="包含 material_id 字段")
    id: Optional[str] = None


class PongMessage(BaseModel):
    type: str = "pong"
    payload: Optional[dict] = None


class ChatTokenEvent(BaseModel):
    type: str = "chat.token"
    content: str


class ChatCompleteEvent(BaseModel):
    type: str = "chat.complete"
    content: str


class EmotionEvent(BaseModel):
    type: str = "emotion.update"
    character_id: str
    mood: float
    mood_delta: float
    cause: str
    expression: str


class ProgressEvent(BaseModel):
    type: str = "progress.update"
    knowledge_point_id: str
    status: str
    mastery: float
    current_day: int
    next_point: Optional[str] = None


class SceneChangeEvent(BaseModel):
    type: str = "scene.change"
    scene_id: str
    scene_name: str
    description: str
    allowed_actions: list


class MaterialStatusEvent(BaseModel):
    type: str = "material.status_changed"
    material_id: int
    status: str
    progress: float
    progress_message: str
    capabilities: dict