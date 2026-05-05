import os
import sys
import shutil
from typing import AsyncGenerator
from io import BytesIO

os.environ["APP_ENV"] = "test"

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi import FastAPI
from pydantic_settings import BaseSettings

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.core.database import Base, Character, Material, Conversation, Message, ModelConfig, BackgroundConfig
from app.core.limiter import limiter


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


class TestSettings(BaseSettings):
    APP_NAME: str = "测试系统"
    DEBUG: bool = True
    DATABASE_URL: str = TEST_DATABASE_URL
    
    MAX_HISTORY_MESSAGES: int = 20
    MAX_HISTORY_TOKENS: int = 4000
    TOKEN_ESTIMATION_RATIO: float = 1.3
    USE_TIKTOKEN: bool = False
    TIKTOKEN_DEFAULT_MODEL: str = "gpt-4"
    ENABLE_HISTORY_SUMMARY: bool = False
    MAX_HISTORY_MESSAGES_VIP: int = 50
    MAX_HISTORY_TOKENS_VIP: int = 8000
    
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    
    CORS_ALLOW_ORIGINS: list = ["http://localhost", "http://127.0.0.1"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    LOG_LEVEL: str = "DEBUG"
    
    DEFAULT_MODEL: str = "gpt-4"
    DEFAULT_PROVIDER: str = "openai"
    
    RATE_LIMIT_STORAGE: str = "memory"
    
    DATA_DIR: str = "./test_data"
    CHARACTERS_DIR: str = "./test_data/characters"
    MATERIALS_DIR: str = "./test_data/materials"
    CONVERSATIONS_DIR: str = "./test_data/conversations"
    UPLOADS_DIR: str = "./test_data/uploads"
    AVATARS_DIR: str = "./test_data/uploads/avatars"
    BACKGROUNDS_DIR: str = "./test_data/uploads/backgrounds"
    
    class Config:
        env_file = ".env.test"


test_settings = TestSettings()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def test_character(test_session: AsyncSession) -> Character:
    character = Character(
        name="苏格拉底导师",
        description="一位精通苏格拉底教学法的AI导师",
        personality="温和、耐心、善于提问引导",
        background="古希腊哲学家苏格拉底的化身，致力于通过提问引导学生思考",
        avatar="🧠",
        avatar_type="emoji",
        is_active=True
    )
    test_session.add(character)
    await test_session.commit()
    await test_session.refresh(character)
    return character


@pytest_asyncio.fixture(scope="function")
async def test_material(test_session: AsyncSession) -> Material:
    material = Material(
        title="Python 基础入门",
        description="Python 编程语言的基础知识",
        content="Python 是一种解释型、高级、通用的编程语言。它的设计哲学强调代码的可读性。"
    )
    test_session.add(material)
    await test_session.commit()
    await test_session.refresh(material)
    return material


@pytest_asyncio.fixture(scope="function")
async def test_conversation(
    test_session: AsyncSession,
    test_character: Character,
    test_material: Material
) -> Conversation:
    conversation = Conversation(
        title="新对话",
        character_id=test_character.id,
        material_id=test_material.id,
        teaching_mode="socratic"
    )
    test_session.add(conversation)
    await test_session.commit()
    await test_session.refresh(conversation)
    return conversation


@pytest_asyncio.fixture(scope="function")
async def test_model_config(test_session: AsyncSession) -> ModelConfig:
    config = ModelConfig(
        provider="openai",
        model_name="gpt-4",
        api_key="test-key",
        base_url=None,
        is_default=True,
        is_active=True
    )
    test_session.add(config)
    await test_session.commit()
    await test_session.refresh(config)
    return config


@pytest_asyncio.fixture(scope="function")
async def test_messages(test_session: AsyncSession, test_conversation: Conversation) -> list[Message]:
    messages = [
        Message(
            conversation_id=test_conversation.id,
            role="user",
            content="什么是 Python？"
        ),
        Message(
            conversation_id=test_conversation.id,
            role="assistant",
            content="很好的问题！在回答之前，你能告诉我你对编程语言了解多少吗？"
        )
    ]
    for msg in messages:
        test_session.add(msg)
    await test_session.commit()
    return messages


@pytest_asyncio.fixture(scope="function")
async def test_background_config(test_session: AsyncSession) -> BackgroundConfig:
    config = BackgroundConfig(
        name="测试背景",
        background_type="color",
        background_value="#ffffff",
        is_default=False,
        is_active=True
    )
    test_session.add(config)
    await test_session.commit()
    await test_session.refresh(config)
    return config


@pytest.fixture(scope="function")
def test_upload_dirs():
    test_dirs = [
        test_settings.DATA_DIR,
        test_settings.AVATARS_DIR,
        test_settings.BACKGROUNDS_DIR,
    ]
    for dir_path in test_dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    yield
    
    if os.path.exists(test_settings.DATA_DIR):
        shutil.rmtree(test_settings.DATA_DIR)


@pytest.fixture(scope="function")
def test_image_bytes():
    img_buffer = BytesIO()
    try:
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
    except ImportError:
        img_buffer = BytesIO(b'fake_png_data')
        img_buffer.seek(0)
    return img_buffer.getvalue()
