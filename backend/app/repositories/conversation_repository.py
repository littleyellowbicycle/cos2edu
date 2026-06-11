from typing import List, Optional, Tuple
from sqlalchemy import select, update, delete, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from models.conversation import Conversation
from models.message import Message
from .base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Conversation)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search(
        self,
        keyword: Optional[str] = None,
        character_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[Conversation], int]:
        stmt = select(Conversation)
        count_stmt = select(func.count(Conversation.id))

        if keyword:
            escaped = keyword.replace('%', '\\%').replace('_', '\\_')
            subq = select(Message.conversation_id).where(
                Message.content.ilike(f"%{escaped}%", escape='\\')
            ).subquery()
            stmt = stmt.where(
                or_(
                    Conversation.title.ilike(f"%{escaped}%", escape='\\'),
                    Conversation.id.in_(select(subq.c.conversation_id)),
                )
            )
            count_stmt = count_stmt.where(
                or_(
                    Conversation.title.ilike(f"%{escaped}%", escape='\\'),
                    Conversation.id.in_(select(subq.c.conversation_id)),
                )
            )

        if character_id:
            stmt = stmt.where(Conversation.character_id == character_id)
            count_stmt = count_stmt.where(Conversation.character_id == character_id)

        total = (await self.session.execute(count_stmt)).scalar() or 0

        result = await self.session.execute(
            stmt.options(selectinload(Conversation.messages))
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, id: int) -> Optional[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .options(selectinload(Conversation.character), selectinload(Conversation.material))
            .filter(Conversation.id == id)
        )
        return result.scalar_one_or_none()

    async def save_summary(
        self,
        conversation_id: int,
        summary: str,
        covered_message_count: int
    ) -> bool:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        update_stmt = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(
                summary=summary,
                summary_covered_message_count=covered_message_count,
                summary_created_at=func.coalesce(Conversation.summary_created_at, now),
                summary_updated_at=now
            )
            .execution_options(synchronize_session="fetch")
        )

        result = await self.session.execute(update_stmt)
        return result.rowcount > 0

    async def clear_summary(self, conversation_id: int) -> bool:
        update_stmt = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(
                summary=None,
                summary_covered_message_count=0,
                summary_created_at=None,
                summary_updated_at=None
            )
            .execution_options(synchronize_session="fetch")
        )

        result = await self.session.execute(update_stmt)
        return result.rowcount > 0

    async def delete_with_messages(self, conversation_id: int) -> bool:
        db_conversation = await self.get_by_id(conversation_id)
        if not db_conversation:
            return False

        await self.session.execute(
            delete(Message).filter(Message.conversation_id == conversation_id)
        )
        await self.session.delete(db_conversation)
        return True