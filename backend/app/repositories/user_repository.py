from app.repositories.base import BaseRepository
from models.user import User


class UserRepository(BaseRepository[User]):
    def __init__(self, session):
        super().__init__(User, session)

    async def get_by_username(self, username: str) -> User | None:
        from sqlalchemy import select
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        from sqlalchemy import select
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()