from .routes import router as api_router
from .chat import router as chat_router
from .pages import router as pages_router
from .upload import router as upload_router

__all__ = ["api_router", "chat_router", "pages_router", "upload_router"]
