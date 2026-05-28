from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.core.database import AsyncSessionLocal
from .character_repository import CharacterRepository
from .material_repository import MaterialRepository
from .conversation_repository import ConversationRepository
from .message_repository import MessageRepository
from .model_config_repository import ModelConfigRepository
from .background_config_repository import BackgroundConfigRepository
from .learning_progress_repository import LearningProgressRepository
from .world_state_repository import WorldStateRepository
from .character_state_repository import CharacterStateRepository
from .syllabus_repository import SyllabusRepository


class UnitOfWork:
    def __init__(self):
        self.session_factory: async_sessionmaker = AsyncSessionLocal
        self._session: Optional[AsyncSession] = None

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            self._session = self.session_factory()
        return self._session

    @property
    def characters(self) -> CharacterRepository:
        return CharacterRepository(self.session)

    @property
    def materials(self) -> MaterialRepository:
        return MaterialRepository(self.session)

    @property
    def conversations(self) -> ConversationRepository:
        return ConversationRepository(self.session)

    @property
    def messages(self) -> MessageRepository:
        return MessageRepository(self.session)

    @property
    def model_configs(self) -> ModelConfigRepository:
        return ModelConfigRepository(self.session)

    @property
    def background_configs(self) -> BackgroundConfigRepository:
        return BackgroundConfigRepository(self.session)

    @property
    def learning_progress(self) -> LearningProgressRepository:
        return LearningProgressRepository(self.session)

    @property
    def world_state(self) -> WorldStateRepository:
        return WorldStateRepository(self.session)

    @property
    def character_state(self) -> CharacterStateRepository:
        return CharacterStateRepository(self.session)

    @property
    def syllabuses(self) -> SyllabusRepository:
        return SyllabusRepository(self.session)

    async def commit(self):
        if self._session:
            await self._session.commit()

    async def rollback(self):
        if self._session:
            await self._session.rollback()

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                await self.commit()
            else:
                await self.rollback()
        finally:
            await self.close()