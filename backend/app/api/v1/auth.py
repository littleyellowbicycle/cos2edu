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


@router.get("/dashboard/student")
async def student_dashboard(user: User = Depends(get_current_user)):
    from app.repositories.unit_of_work import UnitOfWork
    async with UnitOfWork() as uow:
        all_progress = await uow.learning_progress.get_all()
        user_progress = [p for p in all_progress if p.user_id == user.id or p.user_id is None]

        total = len(user_progress)
        mastered = sum(1 for p in user_progress if p.status == "mastered")
        learning = sum(1 for p in user_progress if p.status == "learning")
        locked = sum(1 for p in user_progress if p.status == "locked")

        avg_mastery = sum(p.mastery_level for p in user_progress) / max(total, 1)

        point_details = []
        for p in user_progress:
            point_details.append({
                "point_id": p.knowledge_point_id,
                "status": p.status,
                "mastery_level": round(p.mastery_level, 2),
                "attempts": p.attempts,
                "weak_areas": p.weak_areas or [],
            })

        conversations = await uow.conversations.get_all()
        user_convs = [c for c in conversations if c.user_id == user.id or c.user_id is None]

    return {
        "user": UserResponse.model_validate(user),
        "progress_summary": {
            "total_points": total,
            "mastered": mastered,
            "learning": learning,
            "locked": locked,
            "avg_mastery": round(avg_mastery, 2),
            "completion_rate": round(mastered / max(total, 1) * 100, 1),
        },
        "point_details": point_details,
        "conversation_count": len(user_convs),
    }


@router.get("/dashboard/teacher")
async def teacher_dashboard(user: User = Depends(require_role("teacher", "admin"))):
    from app.repositories.unit_of_work import UnitOfWork
    async with UnitOfWork() as uow:
        all_users = await uow.users.get_all()
        students = [u for u in all_users if u.role == "student"]

        all_progress = await uow.learning_progress.get_all()

        student_stats = []
        for student in students:
            student_progress = [p for p in all_progress if p.user_id == student.id]
            total = len(student_progress)
            mastered = sum(1 for p in student_progress if p.status == "mastered")
            avg_mastery = sum(p.mastery_level for p in student_progress) / max(total, 1)

            student_stats.append({
                "id": student.id,
                "username": student.username,
                "display_name": student.display_name,
                "total_points": total,
                "mastered": mastered,
                "avg_mastery": round(avg_mastery, 2),
                "completion_rate": round(mastered / max(total, 1) * 100, 1),
                "last_login": str(student.last_login_at) if student.last_login_at else None,
            })

        total_points_in_kg = len(set(p.knowledge_point_id for p in all_progress))

    return {
        "total_students": len(students),
        "total_knowledge_points": total_points_in_kg,
        "students": student_stats,
    }