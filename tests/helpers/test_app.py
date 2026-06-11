import os
import sys

os.environ["APP_ENV"] = "test"

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient, ASGITransport


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def create_test_engine():
    return create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


async def create_test_app_with_engine(engine):
    from app.core.database import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    import app.core.database as db_module
    db_module.AsyncSessionLocal = session_factory
    db_module.engine = engine

    import app.repositories.unit_of_work as uow_module
    uow_module.AsyncSessionLocal = session_factory

    from app.api.v1.routes import router as crud_router
    from app.api.v1.chat import router as chat_router
    from app.api.v1.upload import router as upload_router

    from app.core.limiter import limiter

    limiter.reset()
    limiter.enabled = False

    test_app = FastAPI(title="Test App")

    test_app.state.limiter = limiter

    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    test_app.include_router(crud_router, prefix="/api/v1/crud", tags=["crud"])
    test_app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])
    test_app.include_router(upload_router, prefix="/api/v1/upload", tags=["upload"])

    @test_app.middleware("http")
    async def bypass_rate_limit(request: Request, call_next):
        request.state.limiter = None
        response = await call_next(request)
        return response

    return test_app, session_factory


async def get_test_client(test_app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test"
    ) as client:
        yield client