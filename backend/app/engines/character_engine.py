import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CharacterConfig:
    id: str
    name: str
    teaching_style: str
    personality: str
    background: str
    system_prompt_template: str
    emotion_profile: dict = field(default_factory=dict)
    relationship_dynamics: dict = field(default_factory=dict)


class CharacterEngine:
    """角色注册与管理引擎：加载角色配置，提供角色信息"""

    def __init__(self, content_dir: str):
        self._content_dir = Path(content_dir)
        self._characters: dict[str, CharacterConfig] = {}

    def load_characters(self) -> None:
        chars_dir = self._content_dir / "characters"
        if not chars_dir.exists():
            logger.warning(f"Characters directory not found: {chars_dir}")
            return

        for char_file in chars_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(char_file.read_text(encoding="utf-8"))
                if not data:
                    continue
                cid = data.get("id", char_file.stem)
                self._characters[cid] = CharacterConfig(
                    id=cid,
                    name=data.get("name", cid),
                    teaching_style=data.get("teaching_style", ""),
                    personality=data.get("personality", ""),
                    background=data.get("background", ""),
                    system_prompt_template=data.get("system_prompt_template", ""),
                    emotion_profile=data.get("emotion_profile", {}),
                    relationship_dynamics=data.get("relationship_dynamics", {}),
                )
            except Exception as e:
                logger.error(f"Failed to load character {char_file}: {e}")

        logger.info(f"CharacterEngine loaded: {len(self._characters)} characters")

    def get_character(self, character_id: str) -> Optional[CharacterConfig]:
        return self._characters.get(character_id)

    def get_all_characters(self) -> dict[str, CharacterConfig]:
        return dict(self._characters)

    def get_teaching_hint_for_point(
        self, character_id: str, point_teaching_hints: dict
    ) -> str:
        if not point_teaching_hints:
            return ""
        return point_teaching_hints.get(character_id, "")