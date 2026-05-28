from typing import Optional
from app.graph.knowledge_graph import KnowledgeGraph
from app.llm.context_budget import ContextBudget
from app.engines.character_engine import CharacterEngine
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TeachingEngine:
    """教学协作引擎：决定"教什么"和"怎么教" """

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        character_engine: CharacterEngine,
        context_budget: ContextBudget,
    ):
        self.graph = knowledge_graph
        self.character_engine = character_engine
        self.budget = context_budget

    def get_next_teaching_point(
        self,
        mastered_points: set[str],
        current_module: Optional[str] = None,
    ) -> Optional[dict]:
        unlocked = self.graph.get_next_unlocked(mastered_points)
        if not unlocked:
            return None

        if current_module:
            module_points = [
                pid for pid in unlocked
                if self.graph.get_point(pid).module_id == current_module
            ]
            if module_points:
                point_id = module_points[0]
            else:
                point_id = unlocked[0]
        else:
            point_id = unlocked[0]

        point_meta = self.graph.get_point(point_id)
        if not point_meta:
            return None

        return {
            "point_id": point_meta.id,
            "name": point_meta.name,
            "module_name": point_meta.module_name,
            "difficulty": point_meta.difficulty,
            "key_concepts": point_meta.key_concepts,
            "teaching_hints": point_meta.teaching_hints,
            "suggested_questions": point_meta.suggested_questions,
            "exercises": point_meta.exercises,
        }

    def build_teaching_prompt(
        self,
        point_data: dict,
        character_id: str,
        scene_id: str,
        allowed_actions: list[str],
        emotion_summary: str,
        history: list[dict],
        rag_context: str = "",
    ) -> list[dict]:
        character = self.character_engine.get_character(character_id)
        character_persona = character.personality if character else "一位乐于助人的老师"
        if character and character.background:
            character_persona += f"\n背景: {character.background}"

        teaching_hint = self.character_engine.get_teaching_hint_for_point(
            character_id, point_data.get("teaching_hints", {})
        )
        if not teaching_hint and character:
            teaching_hint = f"用{character.name}的风格（{character.teaching_style}）教授这个知识点"

        scene_info = ""
        key_concepts = point_data.get("key_concepts", [])
        suggested_questions = point_data.get("suggested_questions", [])

        return self.budget.build_prompt(
            character_persona=character_persona,
            character_emotion=emotion_summary or "平静、专注",
            scene_id=scene_id,
            allowed_actions=allowed_actions,
            teaching_hint=teaching_hint,
            key_concepts=key_concepts,
            suggested_questions=suggested_questions,
            rag_context=rag_context,
            history=history,
        )

    async def generate_teaching_hint(
        self,
        point_data: dict,
        character_id: str,
        rag_context: str,
    ) -> str:
        character = self.character_engine.get_character(character_id)
        if not character:
            return "请用苏格拉底式提问法引导学生思考这个知识点。"

        prompt = (
            f"你是一位课程助教，正在帮助{character.name}({character.personality})备课。\n\n"
            f"课程内容：{rag_context[:500]}\n"
            f"当前知识点：{point_data.get('name', '')}\n"
            f"核心概念：{', '.join(point_data.get('key_concepts', []))}\n\n"
            f"角色{character.name}的教学风格：{character.teaching_style}\n\n"
            f"请以{character.name}的口吻，给出教授这个知识点的具体教学策略（50字以内）。"
        )

        return prompt