from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.material import Material
from .base import BaseRepository


class MaterialRepository(BaseRepository[Material]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Material)

    async def search_by_title(self, title: str, skip: int = 0, limit: int = 100) -> List[Material]:
        result = await self.session.execute(
            select(Material)
            .filter(Material.title.ilike(f"%{title}%"))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
