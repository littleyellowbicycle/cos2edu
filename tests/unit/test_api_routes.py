import os
import sys
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

os.environ["APP_ENV"] = "test"

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.core.database import Character, Material, Conversation, ModelConfig
from tests.helpers import create_test_app


@pytest.mark.asyncio
class TestCharactersAPI:
    
    async def test_get_characters(self, test_session: AsyncSession, test_character: Character):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/characters")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == test_character.name
    
    async def test_get_character_by_id(self, test_session: AsyncSession, test_character: Character):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/characters/{test_character.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_character.name
    
    async def test_get_character_not_found(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/characters/999")
        
        assert response.status_code == 404
    
    async def test_create_character(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/characters", json={
                "name": "新角色",
                "personality": "温和",
                "avatar": "😊",
                "avatar_type": "emoji"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新角色"
    
    async def test_create_character_missing_fields(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/characters", json={
                "description": "缺少必填字段"
            })
        
        assert response.status_code == 422
    
    async def test_update_character(self, test_session: AsyncSession, test_character: Character):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(f"/api/characters/{test_character.id}", json={
                "name": "更新后的角色"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的角色"
    
    async def test_update_character_not_found(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put("/api/characters/999", json={
                "name": "测试"
            })
        
        assert response.status_code == 404
    
    async def test_delete_character(self, test_session: AsyncSession, test_character: Character):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/api/characters/{test_character.id}")
        
        assert response.status_code == 200


@pytest.mark.asyncio
class TestMaterialsAPI:
    
    async def test_get_materials(self, test_session: AsyncSession, test_material: Material):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/materials")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
    
    async def test_get_material_by_id(self, test_session: AsyncSession, test_material: Material):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/materials/{test_material.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == test_material.title
    
    async def test_get_material_not_found(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/materials/999")
        
        assert response.status_code == 404
    
    async def test_create_material(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/materials", json={
                "title": "新教材",
                "content": "教材内容"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "新教材"
    
    async def test_update_material(self, test_session: AsyncSession, test_material: Material):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(f"/api/materials/{test_material.id}", json={
                "title": "更新后的教材"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后的教材"
    
    async def test_delete_material(self, test_session: AsyncSession, test_material: Material):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/api/materials/{test_material.id}")
        
        assert response.status_code == 200


@pytest.mark.asyncio
class TestConversationsAPI:
    
    async def test_get_conversations(self, test_session: AsyncSession, test_conversation: Conversation):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
    
    async def test_get_conversation_with_messages(self, test_session: AsyncSession, test_conversation: Conversation, test_messages):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/conversations/{test_conversation.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
    
    async def test_get_conversation_not_found(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/conversations/999")
        
        assert response.status_code == 404
    
    async def test_create_conversation(self, test_session: AsyncSession, test_character: Character):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/conversations", json={
                "title": "新对话",
                "character_id": test_character.id,
                "teaching_mode": "socratic"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "新对话"
    
    async def test_update_conversation(self, test_session: AsyncSession, test_conversation: Conversation):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(f"/api/conversations/{test_conversation.id}", json={
                "title": "更新后的标题"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后的标题"
    
    async def test_delete_conversation(self, test_session: AsyncSession, test_conversation: Conversation):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/api/conversations/{test_conversation.id}")
        
        assert response.status_code == 200


@pytest.mark.asyncio
class TestModelConfigsAPI:
    
    async def test_get_model_configs(self, test_session: AsyncSession, test_model_config: ModelConfig):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/model-configs")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
    
    async def test_get_model_config_by_id(self, test_session: AsyncSession, test_model_config: ModelConfig):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/model-configs/{test_model_config.id}")
        
        assert response.status_code == 200
    
    async def test_create_model_config(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/model-configs", json={
                "provider": "openai",
                "model_name": "gpt-4",
                "api_key": "test-key"
            })
        
        assert response.status_code == 200
    
    async def test_update_model_config(self, test_session: AsyncSession, test_model_config: ModelConfig):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(f"/api/model-configs/{test_model_config.id}", json={
                "model_name": "gpt-4-turbo"
            })
        
        assert response.status_code == 200
    
    async def test_delete_model_config(self, test_session: AsyncSession, test_model_config: ModelConfig):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/api/model-configs/{test_model_config.id}")
        
        assert response.status_code == 200


@pytest.mark.asyncio
class TestHealthAPI:
    
    async def test_health_check(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
