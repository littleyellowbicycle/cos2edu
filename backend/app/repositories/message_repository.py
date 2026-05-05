from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.message import Message
from .base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Message)

    async def get_by_conversation(self, conversation_id: int) -> List[Message]:
        result = await self.session.execute(
            select(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return list(result.scalars().all())