import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SceneInfo:
    id: str
    name: str
    description: str
    allowed_actions: list
    mood_modifier: float = 0.0
    bg_color: str = "#1a1a2e"


class WorldStateEngine:
    """世界观状态引擎：管理天数、场景和全局标志"""

    def __init__(self, content_dir: str):
        self._content_dir = Path(content_dir)
        self._scenes: dict[str, SceneInfo] = {}
        self._current_day: int = 1
        self._current_scene: str = "classroom"
        self._global_flags: dict = {}
        self._narrative_phase: str = "prologue"
        self._total_days: int = 90

        self._load_world_settings()

    def _load_world_settings(self) -> None:
        settings_file = self._content_dir / "world" / "settings.yaml"
        if not settings_file.exists():
            logger.warning(f"World settings file not found: {settings_file}")
            return

        try:
            data = yaml.safe_load(settings_file.read_text(encoding="utf-8"))
            world = data.get("world", {})
            self._total_days = world.get("time_scale", 1) * 90
            self._current_scene = world.get("start_scene", "classroom")

            for scene_data in data.get("scenes", []):
                sid = scene_data.get("id", "")
                self._scenes[sid] = SceneInfo(
                    id=sid,
                    name=scene_data.get("name", sid),
                    description=scene_data.get("description", ""),
                    allowed_actions=scene_data.get("allowed_actions", []),
                    mood_modifier=scene_data.get("mood_modifier", 0.0),
                    bg_color=scene_data.get("bg_color", "#1a1a2e"),
                )
            logger.info(f"WorldStateEngine loaded: {len(self._scenes)} scenes")
        except Exception as e:
            logger.error(f"Failed to load world settings: {e}")

    def get_current_scene(self) -> SceneInfo:
        return self._scenes.get(self._current_scene, SceneInfo(
            id="classroom", name="教室",
            description="明亮的教室", allowed_actions=["teach", "question", "discuss"]
        ))

    def get_scene(self, scene_id: str) -> Optional[SceneInfo]:
        return self._scenes.get(scene_id)

    def switch_scene(self, scene_id: str) -> SceneInfo:
        if scene_id in self._scenes:
            self._current_scene = scene_id
            return self._scenes[scene_id]
        logger.warning(f"Unknown scene: {scene_id}")
        return self.get_current_scene()

    def advance_time(self, days: int = 1) -> dict:
        self._current_day += days
        phase = self._determine_phase()
        self._narrative_phase = phase
        return {
            "current_day": self._current_day,
            "total_days": self._total_days,
            "narrative_phase": phase,
            "current_scene": self._current_scene,
            "progress_percent": round(self._current_day / self._total_days * 100, 1),
        }

    def _determine_phase(self) -> str:
        progress = self._current_day / self._total_days
        if progress < 0.33:
            return "phase_1_basics"
        elif progress < 0.67:
            return "phase_2_advanced"
        else:
            return "phase_3_practice"

    def set_global_flag(self, key: str, value) -> None:
        self._global_flags[key] = value

    def get_global_flag(self, key: str, default=None):
        return self._global_flags.get(key, default)

    def get_full_snapshot(self) -> dict:
        scene = self.get_current_scene()
        return {
            "current_day": self._current_day,
            "total_days": self._total_days,
            "current_scene": self._current_scene,
            "scene_info": {
                "name": scene.name,
                "description": scene.description,
                "allowed_actions": scene.allowed_actions,
                "bg_color": scene.bg_color,
            },
            "narrative_phase": self._narrative_phase,
            "global_flags": dict(self._global_flags),
            "progress_percent": round(self._current_day / self._total_days * 100, 1),
        }

    def reset(self) -> None:
        self._current_day = 1
        self._current_scene = "classroom"
        self._global_flags = {}
        self._narrative_phase = "prologue"