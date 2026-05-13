from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.base import Base

ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')


class IRepository(ABC, Generic[ModelType]):
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        pass

    @abstractmethod
    async def create(self, obj_in: dict) -> ModelType:
        pass

    @abstractmethod
    async def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        pass

    @abstractmethod
    async def delete(self, db_obj: ModelType) -> bool:
        pass


class BaseRepository(IRepository[ModelType]):
    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        result = await self.session.execute(
            select(self.model).filter(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.flush()
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        return db_obj

    async def delete(self, db_obj: ModelType) -> bool:
        await self.session.delete(db_obj)
        return True

    async def get_by_field(self, field: str, value) -> Optional[ModelType]:
        result = await self.session.execute(
            select(self.model).filter(getattr(self.model, field) == value)
        )
        return result.scalar_one_or_none()

    async def count(self) -> int:
        result = await self.session.execute(select(self.model))
        return len(result.scalars().all())
