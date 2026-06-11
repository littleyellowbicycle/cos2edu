import os
import sys
from typing import AsyncGenerator
import asyncio

os.environ["APP_ENV"] = "test"

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from models import Character, Material, Conversation, Message, ModelConfig, BackgroundConfig


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(autouse=True)
def suppress_background_tasks(monkeypatch):
    """Prevent fire-and-forget asyncio.create_task from running after test teardown."""
    original_create_task = asyncio.create_task

    def _patched_create_task(coro, *args, **kwargs):
        if hasattr(coro, '__name__') and 'process_material' in coro.__name__:
            coro.close()
            dummy = asyncio.sleep(0)
            return original_create_task(dummy, *args, **kwargs)
        if hasattr(coro, '__name__') and '_generate' in coro.__name__:
            coro.close()
            dummy = asyncio.sleep(0)
            return original_create_task(dummy, *args, **kwargs)
        return original_create_task(coro, *args, **kwargs)

    monkeypatch.setattr(asyncio, 'create_task', _patched_create_task)


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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
        background="古希腊哲学家苏格拉底的化身",
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
async def test_message(test_session: AsyncSession, test_conversation: Conversation) -> Message:
    message = Message(
        conversation_id=test_conversation.id,
        role="user",
        content="什么是 Python？"
    )
    test_session.add(message)
    await test_session.commit()
    await test_session.refresh(message)
    return message


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
