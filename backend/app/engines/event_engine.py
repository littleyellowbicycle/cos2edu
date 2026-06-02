import yaml
import random
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class EventDefinition:
    id: str
    name: str
    event_type: str
    trigger_day: Optional[int] = None
    condition: Optional[str] = None
    description: str = ""
    description_template: str = ""
    scene_change: Optional[str] = None
    probability: float = 0.05
    options: list = field(default_factory=list)


@dataclass
class TriggeredEvent:
    event_id: str
    name: str
    description: str
    scene_change: Optional[str] = None
    options: list = field(default_factory=list)


class EventEngine:
    """事件引擎：检测时间/条件/随机事件触发"""

    def __init__(self, content_dir: str):
        self._content_dir = Path(content_dir)
        self._events: list[EventDefinition] = []
        self._triggered_today: set[str] = set()
        self._last_checked_day: int = 0
        self._load_events()

    def _load_events(self) -> None:
        settings_file = self._content_dir / "world" / "settings.yaml"
        if not settings_file.exists():
            logger.warning(f"World settings file not found: {settings_file}")
            return

        try:
            data = yaml.safe_load(settings_file.read_text(encoding="utf-8"))
            for evt_data in data.get("time_events", []):
                self._events.append(EventDefinition(
                    id=evt_data.get("id", ""),
                    name=evt_data.get("name", ""),
                    event_type="time_based" if evt_data.get("trigger_day") else "condition_based",
                    trigger_day=evt_data.get("trigger_day"),
                    condition=evt_data.get("condition"),
                    description=evt_data.get("description", ""),
                    description_template=evt_data.get("description_template", ""),
                    scene_change=evt_data.get("scene_change"),
                    probability=0.05 if evt_data.get("condition") and "random" in evt_data.get("condition", "") else 1.0,
                    options=evt_data.get("options", []),
                ))
            logger.info(f"EventEngine loaded: {len(self._events)} events")
        except Exception as e:
            logger.error(f"Failed to load events: {e}")

    def check_time_events(self, current_day: int) -> list[TriggeredEvent]:
        triggered = []
        if self._last_checked_day == current_day:
            return triggered

        for event in self._events:
            if event.event_type == "time_based" and event.trigger_day == current_day:
                if event.id not in self._triggered_today:
                    triggered.append(TriggeredEvent(
                        event_id=event.id,
                        name=event.name,
                        description=event.description or event.description_template,
                        scene_change=event.scene_change,
                        options=event.options,
                    ))
                    self._triggered_today.add(event.id)

        self._last_checked_day = current_day
        return triggered

    def check_condition_events(
        self,
        world_state: dict,
        mastered_points: set[str],
        character_states: dict,
    ) -> list[TriggeredEvent]:
        triggered = []
        for event in self._events:
            if event.event_type != "condition_based":
                continue
            if event.id in self._triggered_today:
                continue

            condition = event.condition or ""
            if self._evaluate_condition(condition, world_state, mastered_points, character_states):
                description = event.description
                if event.description_template and "{character_name}" in event.description_template:
                    char_names = list(character_states.keys()) if character_states else ["老师"]
                    description = event.description_template.replace("{character_name}", char_names[0])

                triggered.append(TriggeredEvent(
                    event_id=event.id,
                    name=event.name,
                    description=description,
                    scene_change=event.scene_change,
                    options=event.options,
                ))
                self._triggered_today.add(event.id)

        return triggered

    def check_random_events(self) -> Optional[TriggeredEvent]:
        random_events = [e for e in self._events if e.event_type == "condition_based" and "random" in (e.condition or "")]
        if not random_events:
            return None

        for event in random_events:
            if event.id in self._triggered_today:
                continue
            if random.random() < event.probability:
                self._triggered_today.add(event.id)
                return TriggeredEvent(
                    event_id=event.id,
                    name=event.name,
                    description=event.description,
                    scene_change=event.scene_change,
                    options=event.options,
                )
        return None

    def _evaluate_condition(
        self,
        condition: str,
        world_state: dict,
        mastered_points: set[str],
        character_states: dict,
    ) -> bool:
        if not condition:
            return False

        if "random_probability" in condition:
            return False  # handled by check_random_events

        if "mastery_avg" in condition:
            mastery_avg = world_state.get("progress_percent", 0) / 100.0
            for op in ["<", ">", "<=", ">="]:
                if op in condition:
                    parts = condition.split(op)
                    if len(parts) == 2:
                        threshold = float(parts[1].strip())
                        if op == "<":
                            return mastery_avg < threshold
                        elif op == ">":
                            return mastery_avg > threshold
                        elif op == "<=":
                            return mastery_avg <= threshold
                        elif op == ">=":
                            return mastery_avg >= threshold

        if "current_day" in condition:
            current_day = world_state.get("current_day", 1)
            for op in [">=", "<=", ">", "<"]:
                if op in condition:
                    parts = condition.split(op)
                    if len(parts) == 2:
                        threshold = int(parts[1].strip().split(")")[0].strip())
                        if op == ">":
                            return current_day > threshold
                        elif op == "<":
                            return current_day < threshold

        return False

    def reset_daily(self) -> None:
        self._triggered_today.clear()

    def mark_event_resolved(self, event_id: str) -> None:
        pass

    def reload(self, content_dir: str) -> None:
        self._content_dir = Path(content_dir)
        self._events.clear()
        self._triggered_today.clear()
        self._last_checked_day = 0
        self._load_events()
        logger.info(f"EventEngine reloaded: {len(self._events)} events")