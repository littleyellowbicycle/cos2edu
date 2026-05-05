from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.model_config import ModelConfig
from .base import BaseRepository


class ModelConfigRepository(BaseRepository[ModelConfig]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ModelConfig)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelConfig]:
        result = await self.session.execute(
            select(ModelConfig).filter(ModelConfig.is_active == True).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, id: int) -> Optional[ModelConfig]:
        result = await self.session.execute(
            select(ModelConfig).filter(ModelConfig.id == id)
        )
        return result.scalar_one_or_none()

    async def get_default(self) -> Optional[ModelConfig]:
        result = await self.session.execute(
            select(ModelConfig).filter(
                ModelConfig.is_default == True,
                ModelConfig.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def create(self, obj_in: dict) -> ModelConfig:
        count_result = await self.session.execute(select(self.model.id))
        existing_count = len(count_result.scalars().all())
        is_default = obj_in.get('is_default') or existing_count == 0

        if is_default:
            await self.session.execute(
                update(ModelConfig).values(is_default=False)
            )

        obj_in['is_default'] = is_default
        obj_in['is_active'] = True

        return await super().create(obj_in)

    async def update(self, db_obj: ModelConfig, obj_in: dict) -> ModelConfig:
        if obj_in.get('is_default'):
            await self.session.execute(
                update(ModelConfig).filter(ModelConfig.id != db_obj.id).values(is_default=False)
            )

        return await super().update(db_obj, obj_in)

    async def delete(self, db_obj: ModelConfig) -> bool:
        db_obj.is_active = False
        return True