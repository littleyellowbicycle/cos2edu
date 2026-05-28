from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from models.learning_progress import LearningProgress


class LearningProgressRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, LearningProgress)

    async def get_by_knowledge_point(self, point_id: str) -> Optional[LearningProgress]:
        result = await self.session.execute(
            select(self.model).filter(self.model.knowledge_point_id == point_id)
        )
        return result.scalar_one_or_none()

    async def get_by_status(self, status: str) -> List[LearningProgress]:
        result = await self.session.execute(
            select(self.model).filter(self.model.status == status)
        )
        return result.scalars().all()

    async def get_mastered_point_ids(self) -> List[str]:
        result = await self.session.execute(
            select(self.model.knowledge_point_id).filter(
                self.model.status == "mastered"
            )
        )
        return [row[0] for row in result.all()]