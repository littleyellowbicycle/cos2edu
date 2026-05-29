from fastapi import APIRouter, HTTPException, Request, Depends
from app.core.auth import get_current_user, require_role
from app.core.limiter import limiter
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse, UserUpdate, PasswordChange
from app.services.user_service import UserService
from models.user import User

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
async def register(request: Request, data: UserRegister):
    try:
        return await UserService.register(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/minute")
async def login(request: Request, data: UserLogin):
    try:
        return await UserService.login(data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    request: Request,
    data: UserUpdate,
    user: User = Depends(get_current_user),
):
    try:
        return await UserService.update_profile(user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/change-password")
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    data: PasswordChange,
    user: User = Depends(get_current_user),
):
    try:
        await UserService.change_password(user.id, data.old_password, data.new_password)
        return {"message": "密码修改成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users", response_model=list[UserResponse])
async def list_users(admin: User = Depends(require_role("admin"))):
    from app.repositories.unit_of_work import UnitOfWork
    async with UnitOfWork() as uow:
        users = await uow.users.get_all()
        return [UserResponse.model_validate(u) for u in users]