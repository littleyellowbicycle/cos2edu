import os
import sys
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

os.environ["APP_ENV"] = "test"

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.core.database import Character, Material, Conversation, ModelConfig
from tests.helpers import create_test_app


@pytest.mark.asyncio
class TestEndToEndConversationFlow:
    """端到端对话流程集成测试"""
    
    def get_mock_provider(self, num_messages: int = 1):
        chat_responses = []
        for i in range(num_messages):
            chat_responses.append(f"这是 AI 助手的回复 {i+1}")
            if i == 0:
                chat_responses.append("自动生成的对话标题")
        
        async def mock_chat(*args, **kwargs):
            if chat_responses:
                return chat_responses.pop(0)
            return "这是 AI 助手的默认回复"
        
        async def mock_chat_stream(*args, **kwargs):
            for chunk in ["这", "是", "流", "式", "回", "复"]:
                yield chunk
        
        mock_provider = MagicMock()
        mock_provider.chat = AsyncMock(side_effect=mock_chat)
        mock_provider.chat_stream = mock_chat_stream
        
        return mock_provider
    
    async def test_complete_conversation_flow(self, test_session: AsyncSession):
        """
        测试完整的对话流程：
        1. 创建模型配置
        2. 创建角色
        3. 创建教材
        4. 创建对话
        5. 发送第一条消息（触发标题生成）
        6. 发送更多消息
        7. 验证消息历史
        """
        app = create_test_app(test_session)
        mock_provider = self.get_mock_provider(num_messages=1)
        
        with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/model-configs", json={
                    "provider": "openai",
                    "model_name": "gpt-4",
                    "api_key": "test-api-key",
                    "base_url": None,
                    "is_default": True
                })
                assert response.status_code == 200
                
                response = await client.post("/api/characters", json={
                    "name": "苏格拉底导师",
                    "description": "一位精通苏格拉底教学法的AI导师",
                    "personality": "温和、耐心、善于提问引导",
                    "background": "古希腊哲学家苏格拉底的化身",
                    "avatar": "🧠",
                    "avatar_type": "emoji"
                })
                assert response.status_code == 200
                character = response.json()
                
                response = await client.post("/api/materials", json={
                    "title": "Python 编程基础",
                    "description": "Python 编程语言入门教程",
                    "content": "Python 是一种简单易学的编程语言。变量是存储数据的容器。"
                })
                assert response.status_code == 200
                material = response.json()
                
                response = await client.post("/api/conversations", json={
                    "title": "新对话",
                    "character_id": character["id"],
                    "material_id": material["id"],
                    "teaching_mode": "socratic"
                })
                assert response.status_code == 200
                conversation = response.json()
                conversation_id = conversation["id"]
                
                response = await client.post(f"/api/chat/{conversation_id}", json={
                    "content": "什么是 Python 变量？"
                })
                assert response.status_code == 200
                
                response = await client.get(f"/api/conversations/{conversation_id}")
                assert response.status_code == 200
                conversation_with_msgs = response.json()
                
                assert "messages" in conversation_with_msgs
                messages = conversation_with_msgs["messages"]
                assert len(messages) >= 2
                roles = [msg["role"] for msg in messages]
                assert "user" in roles
                assert "assistant" in roles
    
    async def test_conversation_list_flow(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/characters", json={
                "name": "测试导师",
                "personality": "温和",
                "avatar": "🧠",
                "avatar_type": "emoji"
            })
            assert response.status_code == 200
            character = response.json()
            
            for i in range(3):
                response = await client.post("/api/conversations", json={
                    "title": f"对话 {i+1}",
                    "character_id": character["id"],
                    "teaching_mode": "socratic"
                })
                assert response.status_code == 200
            
            response = await client.get("/api/conversations")
            assert response.status_code == 200
            conversations = response.json()
            assert len(conversations) == 3
    
    async def test_multiple_chat_messages_flow(
        self, 
        test_session: AsyncSession, 
        test_model_config: ModelConfig
    ):
        app = create_test_app(test_session)
        mock_provider = self.get_mock_provider(num_messages=4)
        
        with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/characters", json={
                    "name": "测试导师",
                    "personality": "温和",
                    "avatar": "🧠",
                    "avatar_type": "emoji"
                })
                assert response.status_code == 200
                character = response.json()
                
                response = await client.post("/api/conversations", json={
                    "title": "测试对话",
                    "character_id": character["id"],
                    "teaching_mode": "socratic"
                })
                assert response.status_code == 200
                conversation = response.json()
                conversation_id = conversation["id"]
                
                messages_to_send = [
                    "你好，我想学习 Python",
                    "什么是变量？",
                    "如何定义字符串变量？",
                    "谢谢你的帮助！"
                ]
                
                for msg in messages_to_send:
                    response = await client.post(f"/api/chat/{conversation_id}", json={
                        "content": msg
                    })
                    assert response.status_code == 200
                
                response = await client.get(f"/api/conversations/{conversation_id}")
                assert response.status_code == 200
                conversation_data = response.json()
                
                assert "messages" in conversation_data
                messages = conversation_data["messages"]
                
                user_messages = [m for m in messages if m["role"] == "user"]
                assert len(user_messages) == len(messages_to_send)


@pytest.mark.asyncio
class TestCharacterMaterialIntegrationFlow:
    """角色和教材的集成测试流程"""
    
    async def test_character_crud_flow(self, test_session: AsyncSession):
        """
        测试角色完整 CRUD 流程
        """
        app = create_test_app(test_session)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建角色
            response = await client.post("/api/characters", json={
                "name": "测试导师",
                "description": "这是一个测试角色",
                "personality": "温和、耐心",
                "background": "测试背景故事",
                "avatar": "🤖",
                "avatar_type": "emoji"
            })
            assert response.status_code == 200
            character = response.json()
            character_id = character["id"]
            
            # 获取角色详情
            response = await client.get(f"/api/characters/{character_id}")
            assert response.status_code == 200
            
            # 更新角色
            response = await client.put(f"/api/characters/{character_id}", json={
                "name": "更新后的导师"
            })
            assert response.status_code == 200
            assert response.json()["name"] == "更新后的导师"
            
            # 删除角色
            response = await client.delete(f"/api/characters/{character_id}")
            assert response.status_code == 200
    
    async def test_material_crud_flow(self, test_session: AsyncSession):
        """
        测试教材完整 CRUD 流程
        """
        app = create_test_app(test_session)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建教材
            response = await client.post("/api/materials", json={
                "title": "Python 入门教程",
                "description": "适合初学者的 Python 教程",
                "content": "Python 是一种高级编程语言。"
            })
            assert response.status_code == 200
            material = response.json()
            material_id = material["id"]
            
            # 获取教材详情
            response = await client.get(f"/api/materials/{material_id}")
            assert response.status_code == 200
            
            # 更新教材
            response = await client.put(f"/api/materials/{material_id}", json={
                "title": "Python 编程基础"
            })
            assert response.status_code == 200
            assert response.json()["title"] == "Python 编程基础"
            
            # 删除教材
            response = await client.delete(f"/api/materials/{material_id}")
            assert response.status_code == 200


@pytest.mark.asyncio
class TestModelConfigIntegrationFlow:
    """模型配置的集成测试"""
    
    async def test_multiple_model_configs_flow(self, test_session: AsyncSession):
        """
        测试多模型配置管理
        """
        app = create_test_app(test_session)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            configs_to_create = [
                {"provider": "openai", "model_name": "gpt-4", "api_key": "key-1", "is_default": True},
                {"provider": "anthropic", "model_name": "claude-3", "api_key": "key-2", "is_default": False},
                {"provider": "dashscope", "model_name": "qwen-max", "api_key": "key-3", "is_default": False},
            ]
            
            created_configs = []
            for config_data in configs_to_create:
                response = await client.post("/api/model-configs", json=config_data)
                assert response.status_code == 200
                created_configs.append(response.json())
            
            # 列出所有配置
            response = await client.get("/api/model-configs")
            configs = response.json()
            assert len(configs) == 3
            
            # 验证只有一个默认配置
            default_configs = [c for c in configs if c["is_default"]]
            assert len(default_configs) == 1
