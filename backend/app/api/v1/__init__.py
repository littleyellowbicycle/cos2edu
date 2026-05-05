from fastapi import APIRouter

from .routes import router as crud_router
from .chat import router as chat_router
from .upload import router as upload_router

router = APIRouter()

router.include_router(crud_router, prefix="/crud", tags=["crud"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(upload_router, prefix="/upload", tags=["upload"])

__all__ = ["router", "crud_router", "chat_router", "upload_router"]