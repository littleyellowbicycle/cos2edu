from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timezone

from app.engines.character_engine import CharacterEngine
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class EmotionUpdate:
    character_id: str
    mood: float
    mood_delta: float
    cause: str
    expression: str


class EmotionEngine:
    """情感引擎：计算和更新角色情感状态"""

    def __init__(self, character_engine: CharacterEngine):
        self._character_engine = character_engine
        self._mood_state: dict[str, float] = {}
        self._trust_state: dict[str, float] = {}
        self._initialize_from_characters()

    def _initialize_from_characters(self) -> None:
        for cid, char in self._character_engine.get_all_characters().items():
            self._mood_state[cid] = char.emotion_profile.get("base_mood", 0.7)
            self._trust_state[cid] = char.relationship_dynamics.get("trust_growth_rate", 0.5)

    def get_mood(self, character_id: str) -> float:
        return self._mood_state.get(character_id, 0.7)

    def get_trust(self, character_id: str) -> float:
        return self._trust_state.get(character_id, 0.5)

    def update(
        self,
        character_id: str,
        trigger_event: str,
        trigger_value: float = 0.0,
    ) -> Optional[EmotionUpdate]:
        char = self._character_engine.get_character(character_id)
        if not char:
            return None

        profile = char.emotion_profile
        sensitivity = profile.get("event_sensitivity", {})
        delta = sensitivity.get(trigger_event, trigger_value)

        current_mood = self._mood_state.get(character_id, profile.get("base_mood", 0.7))
        new_mood = max(0.0, min(1.0, current_mood + delta))

        mood_delta = new_mood - current_mood
        self._mood_state[character_id] = new_mood

        trust_config = char.relationship_dynamics
        if trigger_event == "student_correct":
            trust_delta = trust_config.get("trust_growth_rate", 0.01)
        elif trigger_event == "student_wrong":
            trust_delta = -trust_config.get("trust_decay_rate", 0.005)
        else:
            trust_delta = 0.0

        current_trust = self._trust_state.get(character_id, 0.5)
        max_trust = trust_config.get("max_trust", 1.0)
        new_trust = max(0.0, min(max_trust, current_trust + trust_delta))
        self._trust_state[character_id] = new_trust

        expression = self._generate_expression(character_id, new_mood, mood_delta, trigger_event)

        return EmotionUpdate(
            character_id=character_id,
            mood=round(new_mood, 3),
            mood_delta=round(mood_delta, 3),
            cause=trigger_event,
            expression=expression,
        )

    def apply_decay(self, character_id: str, hours_elapsed: float = 1.0) -> Optional[EmotionUpdate]:
        char = self._character_engine.get_character(character_id)
        if not char:
            return None

        decay_rate = char.emotion_profile.get("mood_decay", 0.02)
        base_mood = char.emotion_profile.get("base_mood", 0.7)

        current_mood = self._mood_state.get(character_id, base_mood)
        decay_amount = decay_rate * hours_elapsed
        new_mood = max(base_mood - 0.1, current_mood - decay_amount)

        self._mood_state[character_id] = new_mood

        return EmotionUpdate(
            character_id=character_id,
            mood=round(new_mood, 3),
            mood_delta=round(new_mood - current_mood, 3),
            cause="time_decay",
            expression="恢复了平静" if new_mood > current_mood - 0.01 else "情绪逐渐平复",
        )

    def _generate_expression(self, character_id: str, mood: float, delta: float, event: str) -> str:
        char = self._character_engine.get_character(character_id)
        if not char:
            return ""

        name = char.name

        if delta > 0.05:
            high_expressions = {
                "ganyu": f"{name}眼中闪烁着欣慰的光芒",
                "keqing": f"{name}嘴角微微上扬，眼中闪过一丝满意",
                "march7th": f"{name}兴奋地拍了拍手",
            }
            return high_expressions.get(character_id, f"{name}露出了欣慰的表情")
        elif delta > 0.01:
            avg_expressions = {
                "ganyu": f"{name}温柔地点了点头",
                "keqing": f"{name}微微颔首",
                "march7th": f"{name}开心地笑了起来",
            }
            return avg_expressions.get(character_id, f"{name}微微点头")
        elif delta < -0.05:
            low_expressions = {
                "ganyu": f"{name}眉头微微皱起，但很快恢复了温柔",
                "keqing": f"{name}眼神变得严肃起来",
                "march7th": f"{name}的表情变得认真了一些",
            }
            return low_expressions.get(character_id, f"{name}表情变得严肃")
        elif delta < -0.01:
            avg_low = {
                "ganyu": f"{name}轻轻叹了口气",
                "keqing": f"{name}微微皱眉",
                "march7th": f"{name}若有所思地看着",
            }
            return avg_low.get(character_id, f"{name}面露思考")
        else:
            return f"{name}保持着专注的神情"

    def get_all_states(self) -> dict:
        result = {}
        for cid in self._mood_state:
            char = self._character_engine.get_character(cid)
            result[cid] = {
                "character_id": cid,
                "name": char.name if char else cid,
                "mood": round(self._mood_state[cid], 3),
                "trust": round(self._trust_state.get(cid, 0.5), 3),
                "mood_trend": "stable",
            }
        return result