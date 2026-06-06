from typing import Optional, Any, List
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


class PingMessage(BaseModel):
    type: str = "ping"


class ErrorMessage(BaseModel):
    type: str = "error"
    content: str


class AssessmentStartEvent(BaseModel):
    type: str = "assessment.start"
    payload: dict = Field(..., description="含 point_id, point_name, message")


class AssessmentQuizEvent(BaseModel):
    type: str = "assessment.quiz"
    payload: dict = Field(..., description="含 point_id, point_name, quiz")


class AssessmentResultEvent(BaseModel):
    type: str = "assessment.result"
    payload: dict = Field(..., description="含 point_id, passed, mastery_level, status, feedback, score, attempts")


class AssessmentGenerateMessage(BaseModel):
    type: str = "assessment.generate"
    payload: dict = Field(..., description="含 point_id, character_id")
    id: Optional[str] = None


class AssessmentAnswerMessage(BaseModel):
    type: str = "assessment.answer"
    payload: dict = Field(..., description="含 point_id, character_id, answers, conversation_id")
    id: Optional[str] = None


class EventTriggerEvent(BaseModel):
    type: str = "event.trigger"
    payload: dict = Field(..., description="含 event_id, title, description, scene_change?, options?")


class EventResolvedEvent(BaseModel):
    type: str = "event.resolved"
    payload: dict = Field(..., description="含 event_id, chosen_option")


class NarrativeOptionsEvent(BaseModel):
    type: str = "narrative.options"
    payload: dict = Field(..., description="含 event_id, title, description, options")


class StateFullEvent(BaseModel):
    type: str = "state.full"
    payload: dict = Field(..., description="含 world, characters, progress, activeEvents, narrativeChoices")


class SyllabusActivateMessage(BaseModel):
    type: str = "syllabus.activate"
    payload: dict = Field(..., description="含 material_id")
    id: Optional[str] = None


class SyllabusActivatedEvent(BaseModel):
    type: str = "syllabus.activated"
    payload: dict = Field(..., description="含 material_id, syllabus_name, total_days, knowledge_points, modules")


class TimeAdvanceMessage(BaseModel):
    type: str = "time.advance"
    payload: dict = Field(default_factory=lambda: {"days": 1}, description="含 days")
    id: Optional[str] = None


class TimeAdvancedEvent(BaseModel):
    type: str = "time.advanced"
    payload: dict = Field(..., description="含 current_day, total_days, narrative_phase, current_scene, progress_percent")


class UIRenderEvent(BaseModel):
    type: str = "ui.render"
    id: str = ""
    timestamp: str = ""
    components: list[dict] = []
    metadata: dict = {}


class UIDestroyEvent(BaseModel):
    type: str = "ui.destroy"
    component_ids: list[str] = []


class UIUpdateEvent(BaseModel):
    type: str = "ui.update"
    component_id: str = ""
    props: dict = {}


class UIInteractMessage(BaseModel):
    type: str = "ui.interact"
    payload: dict = Field(..., description="含 component_id, action, value")
    id: Optional[str] = None