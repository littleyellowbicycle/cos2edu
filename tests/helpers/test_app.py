import os
import sys
from typing import AsyncGenerator

os.environ["APP_ENV"] = "test"

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from fastapi import status

from app.core.database import Base
from app.core.config import settings as original_settings
from tests.conftest import test_settings


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"
)


def create_test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


async def get_testing_session_local(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    return session_factory


def create_test_app(session: AsyncSession):
    from app.core import config as app_config
    app_config.settings = test_settings
    
    from app.core.database import AsyncSessionLocal
    AsyncSessionLocal.configure(bind=session.bind)
    
    from app.api.v1.routes import router as api_router
    from app.api.v1.chat import router as chat_router
    from app.api.v1.upload import router as upload_router
    
    test_app = FastAPI(title="Test App")
    
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @test_app.exception_handler(RateLimitExceeded)
    async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "请求过于频繁，请稍后再试",
                "retry_after": "60"
            }
        )
    
    from app.api.v1.upload import get_db as get_db_upload
    
    test_app.dependency_overrides[get_db_upload] = lambda: session
    
    test_app.include_router(api_router, prefix="/api", tags=["api"])
    test_app.include_router(chat_router, prefix="/api", tags=["chat"])
    test_app.include_router(upload_router, prefix="/api", tags=["upload"])
    
    @test_app.get("/health")
    async def health():
        return {"status": "ok"}
    
    return test_app


def restore_settings():
    from app.core import config as app_config
    app_config.settings = original_settings
