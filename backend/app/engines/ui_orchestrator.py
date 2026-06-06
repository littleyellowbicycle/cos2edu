import json
from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timezone


class ComponentSlot(str, Enum):
    INLINE = "inline"
    SIDEBAR = "sidebar"
    OVERLAY = "overlay"
    PANEL = "panel"


class ComponentLifecycle(str, Enum):
    PERSISTENT = "persistent"
    EPHEMERAL = "ephemeral"
    STICKY = "sticky"


class UIComponent(BaseModel):
    id: str
    component: str
    version: str = "1.0"
    props: dict = {}
    slot: ComponentSlot = ComponentSlot.INLINE
    position: str = "after_text"
    lifecycle: ComponentLifecycle = ComponentLifecycle.EPHEMERAL


class UIRenderMessage(BaseModel):
    type: str = "ui.render"
    id: str = ""
    timestamp: str = ""
    components: list[UIComponent] = []
    metadata: dict = {}


class UIDestroyMessage(BaseModel):
    type: str = "ui.destroy"
    component_ids: list[str] = []


class UIUpdateMessage(BaseModel):
    type: str = "ui.update"
    component_id: str = ""
    props: dict = {}


class UIOrchestrator:
    TOOL_DEFINITIONS = [
        {
            "type": "function",
            "function": {
                "name": "show_emotion_card",
                "description": "当角色情绪发生显著变化时展示情绪状态卡片",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mood": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "角色当前情绪值 (0=非常低落, 1=非常开心)",
                        },
                        "trust": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "角色对学生的信任度",
                        },
                        "character_name": {
                            "type": "string",
                            "description": "角色名称",
                        },
                        "reason": {
                            "type": "string",
                            "description": "情绪变化原因（简要）",
                        },
                    },
                    "required": ["mood", "trust"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "show_timeline",
                "description": "当讨论历史事件或时间相关内容时展示时间线",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "year": {"type": "number"},
                                    "date": {"type": "string", "description": "日期文本（如'公元前221年'）"},
                                    "label": {"type": "string"},
                                    "detail": {"type": "string", "description": "补充说明"},
                                },
                                "required": ["label"],
                            },
                            "description": "时间线事件列表",
                        },
                        "title": {"type": "string", "description": "时间线标题"},
                        "active_index": {"type": "integer", "description": "高亮事件索引（-1表示不高亮）", "minimum": -1},
                    },
                    "required": ["events"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "show_quiz",
                "description": "当需要检验学生理解时展示测验表单（支持多题）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "point_id": {"type": "string", "description": "知识点ID"},
                        "point_name": {"type": "string", "description": "知识点名称"},
                        "questions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "question_text": {"type": "string", "description": "题目内容"},
                                    "question_type": {
                                        "type": "string",
                                        "enum": ["choice", "short_answer", "true_false"],
                                        "description": "题目类型",
                                    },
                                    "options": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "选项（仅选择题需要）",
                                    },
                                },
                                "required": ["question_text", "question_type"],
                            },
                            "description": "题目列表",
                        },
                    },
                    "required": ["point_id", "point_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "show_knowledge_graph",
                "description": "当需要展示知识点之间的依赖关系时展示知识图谱",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "highlight": {"type": "string", "description": "高亮的知识点名称"},
                        "title": {"type": "string", "description": "图谱标题"},
                        "depth": {"type": "integer", "description": "展示的依赖深度", "default": 2},
                        "prerequisites": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "name": {"type": "string"},
                                    "mastered": {"type": "boolean"},
                                },
                                "required": ["name"],
                            },
                            "description": "前置知识列表",
                        },
                        "dependencies": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "name": {"type": "string"},
                                },
                                "required": ["name"],
                            },
                            "description": "后续知识列表",
                        },
                        "mastery_level": {"type": "number", "description": "当前知识点掌握度 (0-1)", "minimum": 0, "maximum": 1},
                    },
                    "required": ["highlight"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "switch_scene",
                "description": "当叙事场景发生变化时切换场景",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scene_id": {"type": "string", "description": "场景ID"},
                        "scene_name": {"type": "string", "description": "场景名称"},
                        "description": {"type": "string", "description": "场景描述"},
                        "transition": {
                            "type": "string",
                            "enum": ["fade", "slide", "instant"],
                            "description": "过渡效果",
                            "default": "fade",
                        },
                        "phase": {"type": "string", "description": "时间段（morning/afternoon/evening/night/study/review/exam/break）"},
                        "allowed_actions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "可用操作列表",
                        },
                    },
                    "required": ["scene_id"],
                },
            },
        },
    ]

    TOOL_TO_COMPONENT = {
        "show_emotion_card": ("EmotionCard", ComponentSlot.INLINE, ComponentLifecycle.PERSISTENT),
        "show_timeline": ("Timeline", ComponentSlot.SIDEBAR, ComponentLifecycle.STICKY),
        "show_quiz": ("QuizForm", ComponentSlot.INLINE, ComponentLifecycle.EPHEMERAL),
        "show_knowledge_graph": ("KnowledgeGraph", ComponentSlot.PANEL, ComponentLifecycle.STICKY),
        "switch_scene": ("SceneCard", ComponentSlot.OVERLAY, ComponentLifecycle.EPHEMERAL),
    }

    PROP_RENAMES = {
        "character_name": "characterName",
        "mood_direction": "moodDirection",
        "point_id": "pointId",
        "point_name": "pointName",
        "active_index": "activeIndex",
        "mastery_level": "masteryLevel",
        "scene_id": "sceneId",
        "scene_name": "sceneName",
        "allowed_actions": "allowedActions",
    }

    def _camel_case_props(self, props: dict) -> dict:
        out = {}
        for k, v in props.items():
            key = self.PROP_RENAMES.get(k, k)
            if isinstance(v, list):
                out[key] = [self._camel_case_props(item) if isinstance(item, dict) else item for item in v]
            elif isinstance(v, dict):
                out[key] = self._camel_case_props(v)
            else:
                out[key] = v
        return out

    def convert_tool_calls(self, tool_calls: list) -> list[UIComponent]:
        components = []
        for tc in tool_calls:
            if hasattr(tc, 'function') and tc.function is not None:
                func_name = tc.function.name or ''
                args_str = tc.function.arguments or '{}'
                tc_id = getattr(tc, 'id', f'comp_{len(components)}')
            else:
                func_name = tc.get('name', '') or tc.get('function', {}).get('name', '')
                args_str = tc.get('arguments', '{}') or tc.get('function', {}).get('arguments', '{}')
                tc_id = tc.get('id', f'comp_{len(components)}')

            if func_name not in self.TOOL_TO_COMPONENT:
                continue

            comp_name, slot, lifecycle = self.TOOL_TO_COMPONENT[func_name]
            try:
                args = json.loads(args_str) if isinstance(args_str, str) else args_str
            except (json.JSONDecodeError, TypeError):
                args = {}

            components.append(UIComponent(
                id=f"comp_{tc_id}",
                component=comp_name,
                props=self._camel_case_props(args),
                slot=slot,
                lifecycle=lifecycle,
            ))

        return components

    def build_ui_render_message(self, components: list[UIComponent], msg_id: str = "") -> dict:
        return UIRenderMessage(
            id=msg_id or f"ui_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            components=components,
        ).model_dump()