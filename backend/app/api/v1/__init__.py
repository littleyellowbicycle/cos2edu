from fastapi import APIRouter

from .routes import router as crud_router
from .chat import router as chat_router
from .upload import router as upload_router
from .ws import router as ws_router
from .curriculum import router as curriculum_router
from .auth import router as auth_router

router = APIRouter()

router.include_router(crud_router, prefix="/crud", tags=["crud"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(upload_router, prefix="/upload", tags=["upload"])
router.include_router(ws_router, prefix="/ws", tags=["websocket"])
router.include_router(curriculum_router, prefix="/curriculum", tags=["curriculum"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])

__all__ = ["router", "crud_router", "chat_router", "upload_router", "ws_router", "curriculum_router", "auth_router"]