from fastapi import APIRouter

from .routes import router as crud_router
from .chat import router as chat_router
from .upload import router as upload_router
from .pages import router as pages_router

router = APIRouter()

router.include_router(crud_router, prefix="/crud", tags=["crud"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(upload_router, tags=["upload"])
router.include_router(pages_router, prefix="/pages", tags=["pages"])

__all__ = ["router", "crud_router", "chat_router", "upload_router", "pages_router"]