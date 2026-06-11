import asyncio
from datetime import datetime
from typing import Optional

from sqlalchemy import select

from app.core.logging_config import get_logger
from app.repositories.unit_of_work import UnitOfWork

logger = get_logger(__name__)


class StateManager:
    """分级状态落盘管理器：Critical 立即写，Soft 定时批量"""

    CRITICAL_EVENTS = {
        "mastery_change",
        "scene_change",
        "narrative_choice",
        "review_status_change",
        "assessment_result",
    }
    BATCH_SIZE = 10
    FLUSH_INTERVAL = 60

    def __init__(self):
        self._soft_buffer: list[tuple] = []
        self._uow_factory = UnitOfWork
        self._running = False

    async def update(self, event_type: str, data: dict) -> None:
        if event_type in self.CRITICAL_EVENTS:
            await self._persist_immediately(event_type, data)
        else:
            await self._buffer_for_batch(event_type, data)

    async def _persist_immediately(self, event_type: str, data: dict) -> None:
        try:
            async with self._uow_factory() as uow:
                if event_type == "mastery_change":
                    await self._update_mastery(uow, data)
                elif event_type == "scene_change":
                    await self._update_scene(uow, data)
                elif event_type == "narrative_choice":
                    await self._update_global_flag(uow, data)
                elif event_type == "review_status_change":
                    await self._update_review_status(uow, data)
                elif event_type == "assessment_result":
                    await self._update_mastery(uow, data)
        except Exception as e:
            logger.error(f"Critical persist failed for {event_type}: {e}")

    async def _buffer_for_batch(self, event_type: str, data: dict) -> None:
        self._soft_buffer.append((event_type, data, datetime.now()))
        if len(self._soft_buffer) >= self.BATCH_SIZE:
            await self._flush_soft_buffer()

    async def _flush_soft_buffer(self) -> None:
        if not self._soft_buffer:
            return
        buffer = self._soft_buffer.copy()
        self._soft_buffer.clear()

        try:
            async with self._uow_factory() as uow:
                for event_type, data, ts in buffer:
                    if event_type == "mood_change":
                        await self._update_mood(uow, data)
                    elif event_type == "trust_change":
                        await self._update_trust(uow, data)
                    elif event_type == "time_advance":
                        await self._update_day(uow, data)
        except Exception as e:
            logger.error(f"Soft buffer flush failed: {e}")

    async def _update_mastery(self, uow, data: dict) -> None:
        point_id = data.get("point_id")
        mastery = data.get("mastery", 0.0)
        status = data.get("status", "learning")
        attempts = data.get("attempts")
        weak_areas = data.get("weak_areas")
        progress = await uow.learning_progress.get_by_field("knowledge_point_id", point_id)
        if progress:
            update_data = {
                "mastery_level": mastery,
                "status": status,
                "last_reviewed_at": datetime.now(),
            }
            if attempts is not None:
                update_data["attempts"] = attempts
            if weak_areas is not None:
                update_data["weak_areas"] = weak_areas
            await uow.learning_progress.update(progress, update_data)
        else:
            create_data = {
                "knowledge_point_id": point_id,
                "mastery_level": mastery,
                "status": status,
                "last_reviewed_at": datetime.now(),
            }
            if attempts is not None:
                create_data["attempts"] = attempts
            if weak_areas is not None:
                create_data["weak_areas"] = weak_areas
            await uow.learning_progress.create(create_data)

    async def _update_scene(self, uow, data: dict) -> None:
        from models.world_state import WorldState
        ws = await uow.session.get(WorldState, 1)
        if ws:
            ws.current_scene = data.get("scene_id", ws.current_scene)
            if "narrative_phase" in data:
                ws.narrative_phase = data["narrative_phase"]

    async def _update_global_flag(self, uow, data: dict) -> None:
        from models.world_state import WorldState
        ws = await uow.session.get(WorldState, 1)
        if ws and ws.global_flags:
            flags = ws.global_flags if isinstance(ws.global_flags, dict) else {}
            flags[data["flag_key"]] = data["flag_value"]
            ws.global_flags = flags

    async def _update_review_status(self, uow, data: dict) -> None:
        material = await uow.materials.get_by_id(data.get("material_id", 0))
        if material:
            await uow.materials.update(material, {
                "review_status": data.get("review_status"),
            })

    async def _update_mood(self, uow, data: dict) -> None:
        from models.character_state import CharacterState
        char_id = data.get("character_id")
        result = await uow.session.execute(
            select(CharacterState).where(
                CharacterState.character_id == char_id
            )
        )
        cs = result.scalar_one_or_none()
        if cs:
            cs.current_mood = data.get("mood", cs.current_mood)

    async def _update_trust(self, uow, data: dict) -> None:
        from models.character_state import CharacterState
        char_id = data.get("character_id")
        result = await uow.session.execute(
            select(CharacterState).where(
                CharacterState.character_id == char_id
            )
        )
        cs = result.scalar_one_or_none()
        if cs:
            cs.trust_level = data.get("trust", cs.trust_level)

    async def _update_day(self, uow, data: dict) -> None:
        from models.world_state import WorldState
        ws = await uow.session.get(WorldState, 1)
        if ws:
            ws.current_day = data.get("current_day", ws.current_day)

    async def start_periodic_flush(self) -> None:
        self._running = True
        while self._running:
            await asyncio.sleep(self.FLUSH_INTERVAL)
            await self._flush_soft_buffer()

    async def shutdown_flush(self) -> None:
        self._running = False
        await self._flush_soft_buffer()