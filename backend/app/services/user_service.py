from datetime import datetime, timezone
from app.core.auth import hash_password, verify_password, create_access_token
from app.core.logging_config import get_logger
from app.repositories.unit_of_work import UnitOfWork
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse, UserUpdate
from models.user import User

logger = get_logger(__name__)


class UserService:
    @staticmethod
    async def register(data: UserRegister) -> TokenResponse:
        async with UnitOfWork() as uow:
            existing = await uow.users.get_by_username(data.username)
            if existing:
                raise ValueError(f"用户名 '{data.username}' 已存在")

            existing_email = await uow.users.get_by_email(data.email)
            if existing_email:
                raise ValueError(f"邮箱 '{data.email}' 已注册")

            if data.role not in ("student", "teacher", "admin"):
                raise ValueError("角色必须是 student、teacher 或 admin")

            user = User(
                username=data.username,
                email=data.email,
                hashed_password=hash_password(data.password),
                display_name=data.display_name or data.username,
                role=data.role,
            )
            created = await uow.users.create(user)
            await uow.commit()

            token = create_access_token({"sub": str(created.id), "role": created.role})

            return TokenResponse(
                access_token=token,
                user=UserResponse.model_validate(created),
            )

    @staticmethod
    async def login(data: UserLogin) -> TokenResponse:
        async with UnitOfWork() as uow:
            user = await uow.users.get_by_username(data.username)
            if not user or not verify_password(data.password, user.hashed_password):
                raise ValueError("用户名或密码错误")

            if not user.is_active:
                raise ValueError("账户已禁用")

            user.last_login_at = datetime.now(timezone.utc)
            await uow.users.update(user, {"last_login_at": user.last_login_at})
            await uow.commit()

            token = create_access_token({"sub": str(user.id), "role": user.role})

            return TokenResponse(
                access_token=token,
                user=UserResponse.model_validate(user),
            )

    @staticmethod
    async def get_profile(user_id: int) -> UserResponse:
        async with UnitOfWork() as uow:
            user = await uow.users.get_by_id(user_id)
            if not user:
                raise ValueError("用户不存在")
            return UserResponse.model_validate(user)

    @staticmethod
    async def update_profile(user_id: int, data: UserUpdate) -> UserResponse:
        async with UnitOfWork() as uow:
            user = await uow.users.get_by_id(user_id)
            if not user:
                raise ValueError("用户不存在")

            update_data = {}
            if data.display_name is not None:
                update_data["display_name"] = data.display_name
            if data.email is not None:
                existing_email = await uow.users.get_by_email(data.email)
                if existing_email and existing_email.id != user_id:
                    raise ValueError("邮箱已被其他用户使用")
                update_data["email"] = data.email
            if data.avatar is not None:
                update_data["avatar"] = data.avatar
            if data.avatar_type is not None:
                update_data["avatar_type"] = data.avatar_type

            updated = await uow.users.update(user, update_data)
            await uow.commit()
            return UserResponse.model_validate(updated)

    @staticmethod
    async def change_password(user_id: int, old_password: str, new_password: str) -> bool:
        async with UnitOfWork() as uow:
            user = await uow.users.get_by_id(user_id)
            if not user:
                raise ValueError("用户不存在")

            if not verify_password(old_password, user.hashed_password):
                raise ValueError("原密码错误")

            await uow.users.update(user, {"hashed_password": hash_password(new_password)})
            await uow.commit()
            return True