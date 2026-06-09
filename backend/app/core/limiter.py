from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def get_storage_uri() -> str:
    if settings.RATE_LIMIT_STORAGE == "redis":
        try:
            import redis
        except ImportError:
            return "memory://"
        
        if settings.REDIS_URL:
            return settings.REDIS_URL
        
        if settings.REDIS_HOST and settings.REDIS_PASSWORD:
            return f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        if settings.REDIS_HOST:
            return f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        return "memory://"
    
    return "memory://"


storage_uri = get_storage_uri()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri
)
