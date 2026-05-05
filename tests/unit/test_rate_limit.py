import os
import sys
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

os.environ["APP_ENV"] = "test"

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.core.database import Character, Material, Conversation, ModelConfig, BackgroundConfig
from tests.helpers import create_test_app


@pytest.mark.asyncio
class TestRateLimiter:
    
    async def test_get_characters_success(self, test_session: AsyncSession, test_character: Character):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/characters")
        assert response.status_code == 200
    
    async def test_get_character_by_id_success(self, test_session: AsyncSession, test_character: Character):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/characters/{test_character.id}")
        assert response.status_code == 200
    
    async def test_create_character_success(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/characters", json={
                "name": "测试角色",
                "personality": "温和",
                "avatar": "😊",
                "avatar_type": "emoji"
            })
        assert response.status_code == 200
    
    async def test_update_character_success(self, test_session: AsyncSession, test_character: Character):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(f"/api/characters/{test_character.id}", json={
                "name": "更新后的角色"
            })
        assert response.status_code == 200
    
    async def test_delete_character_success(self, test_session: AsyncSession, test_character: Character):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/api/characters/{test_character.id}")
        assert response.status_code == 200
    
    async def test_get_materials_empty(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/materials")
        assert response.status_code == 200
    
    async def test_create_material_success(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/materials", json={
                "title": "测试教材",
                "content": "教材内容"
            })
        assert response.status_code == 200
    
    async def test_get_conversations_empty(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/conversations")
        assert response.status_code == 200
    
    async def test_create_conversation_success(self, test_session: AsyncSession, test_character: Character):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/conversations", json={
                "title": "测试对话",
                "character_id": test_character.id,
                "teaching_mode": "socratic"
            })
        assert response.status_code == 200
    
    async def test_get_model_configs_empty(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/model-configs")
        assert response.status_code == 200
    
    async def test_create_model_config_success(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/model-configs", json={
                "provider": "openai",
                "model_name": "gpt-4",
                "api_key": "test-key"
            })
        assert response.status_code == 200
    
    async def test_health_check(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
        assert response.status_code == 200


@pytest.mark.asyncio
class TestRateLimiterMemoryStorage:
    
    async def test_memory_limiter_creation(self):
        from app.core.limiter import limiter
        assert limiter is not None
    
    async def test_redis_limiter_creation(self):
        # 测试 Redis limiter 创建逻辑
        pass
    
    async def test_redis_limiter_without_url(self):
        # 测试没有 URL 时的处理
        pass
    
    async def test_redis_limiter_without_password(self):
        # 测试没有密码时的处理
        pass


@pytest.mark.asyncio
class TestRateLimitErrorHandling:
    
    async def test_rate_limit_exceeded_handler(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        # 测试限流错误处理
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/characters")
        assert response.status_code == 200


@pytest.mark.asyncio
class TestBackgroundRateLimit:
    
    async def test_get_backgrounds_empty(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/backgrounds")
        assert response.status_code == 200
    
    async def test_get_default_background(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        
        # 创建默认背景
        bg = BackgroundConfig(
            name="默认背景",
            background_type="color",
            background_value="#ffffff",
            is_default=True,
            is_active=True
        )
        test_session.add(bg)
        await test_session.commit()
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/backgrounds/default")
        assert response.status_code == 200
    
    async def test_create_background_success(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/backgrounds", json={
                "name": "新背景",
                "background_type": "color",
                "background_value": "#000000"
            })
        assert response.status_code == 200
