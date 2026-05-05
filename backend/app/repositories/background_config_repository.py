from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.background_config import BackgroundConfig
from .base import BaseRepository


class BackgroundConfigRepository(BaseRepository[BackgroundConfig]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, BackgroundConfig)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[BackgroundConfig]:
        result = await self.session.execute(
            select(BackgroundConfig).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, id: int) -> Optional[BackgroundConfig]:
        result = await self.session.execute(
            select(BackgroundConfig).filter(BackgroundConfig.id == id)
        )
        return result.scalar_one_or_none()

    async def get_default(self) -> Optional[BackgroundConfig]:
        result = await self.session.execute(
            select(BackgroundConfig).filter(
                BackgroundConfig.is_default == True,
                BackgroundConfig.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def create(self, obj_in: dict) -> BackgroundConfig:
        if obj_in.get('is_default'):
            await self.session.execute(
                update(BackgroundConfig).values(is_default=False)
            )

        obj_in['is_active'] = True

        return await super().create(obj_in)

    async def update(self, db_obj: BackgroundConfig, obj_in: dict) -> BackgroundConfig:
        if obj_in.get('is_default'):
            await self.session.execute(
                update(BackgroundConfig).filter(BackgroundConfig.id != db_obj.id).values(is_default=False)
            )

        return await super().update(db_obj, obj_in)