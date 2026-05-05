from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.character import Character
from .base import BaseRepository


class CharacterRepository(BaseRepository[Character]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Character)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Character]:
        result = await self.session.execute(
            select(Character).filter(Character.is_active == True).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_by_id(self, id: int) -> Optional[Character]:
        result = await self.session.execute(
            select(Character).filter(
                Character.id == id,
                Character.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Character]:
        result = await self.session.execute(
            select(Character).filter(
                Character.name == name,
                Character.is_active == True
            )
        )
        return result.scalar_one_or_none()
