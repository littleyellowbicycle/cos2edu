from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from models.character_state import CharacterState


class CharacterStateRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, CharacterState)

    async def get_by_character_id(self, character_id: int) -> Optional[CharacterState]:
        result = await self.session.execute(
            select(self.model).filter(self.model.character_id == character_id)
        )
        return result.scalar_one_or_none()

    async def update_mood(self, character_id: int, mood: float) -> None:
        cs = await self.get_by_character_id(character_id)
        if cs:
            cs.current_mood = mood

    async def update_trust(self, character_id: int, trust: float) -> None:
        cs = await self.get_by_character_id(character_id)
        if cs:
            cs.trust_level = trust