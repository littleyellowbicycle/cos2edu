import json
from typing import Optional, AsyncIterator
from datetime import datetime

from app.graph.knowledge_graph import KnowledgeGraph
from app.engines.world_state_engine import WorldStateEngine
from app.engines.teaching_engine import TeachingEngine
from app.engines.character_engine import CharacterEngine
from app.state.state_manager import StateManager
from app.services.chat_service import ChatService
from app.repositories.unit_of_work import UnitOfWork
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class NarrativeEngine:
    """叙事编排引擎：总调度，协调各引擎"""

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        world_state_engine: WorldStateEngine,
        character_engine: CharacterEngine,
        teaching_engine: TeachingEngine,
        state_manager: StateManager,
    ):
        self.graph = knowledge_graph
        self.world = world_state_engine
        self.characters = character_engine
        self.teaching = teaching_engine
        self.state_manager = state_manager

    async def handle_chat_message(
        self,
        conversation_id: int,
        user_message: str,
        character_id: str,
        model_config=None,
    ) -> AsyncIterator[str]:
        """处理聊天消息，返回 SSE 事件流"""
        try:
            async with UnitOfWork() as uow:
                conversation = await uow.conversations.get_by_id(conversation_id)
                if not conversation:
                    raise ValueError(f"Conversation {conversation_id} not found")

                await uow.messages.create({
                    "conversation_id": conversation_id,
                    "role": "user",
                    "content": user_message,
                })

                mastered = await self._get_mastered_points(uow)
                point_data = self.teaching.get_next_teaching_point(mastered)

                scene = self.world.get_current_scene()

                emotion_summary = "平静、专注"

                rag_context = ""
                if conversation.material and conversation.material.content:
                    rag_context = conversation.material.content[:2000]

                history_messages = []
                history = await uow.messages.get_by_conversation(conversation_id)
                for msg in history[-20:]:
                    history_messages.append({"role": msg.role, "content": msg.content})

                if point_data:
                    messages = self.teaching.build_teaching_prompt(
                        point_data=point_data,
                        character_id=character_id,
                        scene_id=scene.id,
                        allowed_actions=scene.allowed_actions,
                        emotion_summary=emotion_summary,
                        history=history_messages,
                        rag_context=rag_context,
                    )
                else:
                    messages = self._build_default_prompt(
                        character_id=character_id,
                        history=history_messages,
                        rag_context=rag_context,
                    )

                config_dict = None
                if model_config:
                    config_dict = {
                        "provider": model_config.provider,
                        "model_name": model_config.model_name,
                        "api_key": model_config.api_key,
                        "base_url": model_config.base_url,
                        "group_id": getattr(model_config, "group_id", None),
                    }

                full_response = ""
                async for chunk in ChatService.chat_stream(
                    conversation_id=conversation_id,
                    user_message=user_message,
                    model_config=model_config,
                ):
                    full_response += chunk if not chunk.startswith("data:") else ""
                    yield json.dumps({"type": "chat.token", "content": chunk}, ensure_ascii=False)

                yield json.dumps({"type": "chat.complete", "content": full_response}, ensure_ascii=False)

        except Exception as e:
            logger.error(f"NarrativeEngine chat error: {e}")
            yield json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False)

    def _build_default_prompt(
        self,
        character_id: str,
        history: list[dict],
        rag_context: str = "",
    ) -> list[dict]:
        character = self.characters.get_character(character_id)
        system = "你是一位苏格拉底式教学助手，通过提问引导学生自主思考。"

        if character:
            system = f"{character.personality}\n背景: {character.background}"

        messages = [{"role": "system", "content": system}]
        if rag_context:
            messages.append({"role": "system", "content": f"参考资料:\n{rag_context[:2000]}"})

        messages.extend(history[-20:])
        return messages

    async def _get_mastered_points(self, uow) -> set[str]:
        from models.learning_progress import LearningProgress
        from sqlalchemy import select
        result = await uow.session.execute(
            select(LearningProgress).where(
                LearningProgress.status == "mastered"
            )
        )
        points = result.scalars().all()
        return {p.knowledge_point_id for p in points}

    async def get_full_snapshot(self) -> dict:
        """返回完整状态快照，用于 WS 重连对账"""
        world_snapshot = self.world.get_full_snapshot()

        async with UnitOfWork() as uow:
            from models.character_state import CharacterState
            from sqlalchemy import select
            result = await uow.session.execute(select(CharacterState))
            char_states = result.scalars().all()
            characters_snapshot = {}
            for cs in char_states:
                char = self.characters.get_character(str(cs.character_id))
                characters_snapshot[str(cs.character_id)] = {
                    "name": char.name if char else str(cs.character_id),
                    "mood": cs.current_mood,
                    "trust_level": cs.trust_level,
                }

            mastered = await self._get_mastered_points(uow)
            all_points = self.graph.get_all_points()
            unlocked = self.graph.get_next_unlocked(mastered)

        return {
            "world": world_snapshot,
            "characters": characters_snapshot,
            "progress": {
                "mastered_count": len(mastered),
                "total_count": len(all_points),
                "mastered_points": list(mastered),
                "next_point": unlocked[0] if unlocked else None,
            },
        }