from typing import Optional, List
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from models.message import Message


class MessageSearchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_messages(
        self,
        query: str,
        conversation_id: Optional[int] = None,
        role: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[Message], int]:
        escaped = query.replace('%', '\\%').replace('_', '\\_')
        count_stmt = select(func.count(Message.id)).where(
            Message.content.ilike(f"%{escaped}%", escape='\\')
        )
        if conversation_id:
            count_stmt = count_stmt.where(Message.conversation_id == conversation_id)
        if role:
            count_stmt = count_stmt.where(Message.role == role)

        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = (
            select(Message)
            .where(Message.content.ilike(f"%{escaped}%", escape='\\'))
            .order_by(Message.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if conversation_id:
            stmt = stmt.where(Message.conversation_id == conversation_id)
        if role:
            stmt = stmt.where(Message.role == role)

        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        return messages, total