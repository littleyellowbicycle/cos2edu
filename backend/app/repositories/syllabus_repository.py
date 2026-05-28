from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from models.syllabus import Syllabus


class SyllabusRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Syllabus)

    async def get_by_material_id(self, material_id: int) -> Optional[Syllabus]:
        result = await self.session.execute(
            select(self.model).filter(self.model.material_id == material_id)
        )
        return result.scalar_one_or_none()

    async def get_approved(self):
        result = await self.session.execute(
            select(self.model).filter(self.model.review_status == "approved")
        )
        return result.scalars().all()