from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from models.world_state import WorldState


class WorldStateRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, WorldState)

    async def get_current(self) -> Optional[WorldState]:
        result = await self.session.execute(
            select(self.model).filter(self.model.id == 1)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self) -> WorldState:
        ws = await self.get_current()
        if not ws:
            ws = await self.create({"current_day": 1, "current_scene": "classroom"})
        return ws