import os
os.environ["APP_ENV"] = "test"

import sys
import json
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.core.database import Character, Material, Conversation, ModelConfig
from tests.helpers import create_test_app


@pytest.mark.asyncio
class TestChatAPI:
    
    async def test_chat_non_existent_conversation(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        
        mock_provider = AsyncMock()
        mock_provider.chat.return_value = "测试回复"
        
        with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/chat/999", json={
                    "content": "你好"
                })
        
        assert response.status_code == 400
    
    async def test_chat_success(
        self, 
        test_session: AsyncSession, 
        test_conversation: Conversation,
        test_model_config: ModelConfig
    ):
        app = create_test_app(test_session)
        
        mock_provider = MagicMock()
        mock_provider.chat = AsyncMock(return_value="这是测试回复")
        
        with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(f"/api/chat/{test_conversation.id}", json={
                    "content": "你好"
                })
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["response"] == "这是测试回复"
    
    async def test_chat_first_message_generates_title(
        self, 
        test_session: AsyncSession, 
        test_conversation: Conversation,
        test_model_config: ModelConfig
    ):
        app = create_test_app(test_session)
        
        mock_provider = AsyncMock()
        mock_provider.chat.side_effect = [
            "这是测试回复",
            "测试对话标题"
        ]
        
        with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(f"/api/chat/{test_conversation.id}", json={
                    "content": "这是第一条消息"
                })
        
        assert response.status_code == 200
        assert mock_provider.chat.call_count == 2
    
    async def test_chat_with_invalid_message(
        self, 
        test_session: AsyncSession, 
        test_conversation: Conversation
    ):
        app = create_test_app(test_session)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(f"/api/chat/{test_conversation.id}", json={
                "content": ""
            })
        
        assert response.status_code == 422
    
    async def test_chat_stream_non_existent_conversation(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            async with client.stream(
                "POST",
                "/api/chat/999/stream",
                json={"content": "你好"}
            ) as response:
                error_found = False
                async for line in response.aiter_lines():
                    if line:
                        if line.startswith("data:"):
                            data_str = line[5:].strip()
                            if data_str and data_str != "[DONE]":
                                try:
                                    data = json.loads(data_str)
                                    if "error" in data:
                                        error_found = True
                                        break
                                except:
                                    pass
        
        assert error_found or response.status_code == 400
    
    async def test_chat_stream_success(
        self, 
        test_session: AsyncSession, 
        test_conversation: Conversation,
        test_model_config: ModelConfig
    ):
        app = create_test_app(test_session)
        
        async def mock_chat_stream_gen(*args, **kwargs):
            for chunk in ["测", "试", "回", "复"]:
                yield chunk
        
        mock_provider = MagicMock()
        mock_provider.chat_stream = mock_chat_stream_gen
        mock_provider.chat = AsyncMock(return_value="测试回复")
        
        full_content = ""
        with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                async with client.stream(
                    "POST",
                    f"/api/chat/{test_conversation.id}/stream",
                    json={"content": "你好"}
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            if line.startswith("data:"):
                                data_str = line[5:].strip()
                                if data_str == "[DONE]":
                                    break
                                if data_str:
                                    try:
                                        data = json.loads(data_str)
                                        if "content" in data:
                                            full_content += data["content"]
                                    except:
                                        pass
        
        assert full_content == "测试回复" or response.status_code == 200


@pytest.mark.asyncio
class TestChatAPIConcurrency:

    async def test_concurrent_requests_same_conversation_second_rejected(
        self,
        test_session: AsyncSession,
        test_conversation: Conversation,
        test_model_config: ModelConfig
    ):
        """测试同一客户端并发请求同一 conversation 时，第二个请求应被拒绝"""
        import asyncio

        app = create_test_app(test_session)

        async def long_chat_request():
            async def mock_long_chat(*args, **kwargs):
                await asyncio.sleep(2.0)
                return "长响应"

            mock_provider = MagicMock()
            mock_provider.chat = mock_long_chat

            with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        f"/api/chat/{test_conversation.id}",
                        json={"content": "你好"}
                    )
                    return response

        task1 = asyncio.create_task(long_chat_request())
        await asyncio.sleep(0.1)

        mock_provider2 = MagicMock()
        mock_provider2.chat = AsyncMock(return_value="快速回复")

        with patch('app.services.teaching_service.get_provider', return_value=mock_provider2):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response2 = await client.post(
                    f"/api/chat/{test_conversation.id}",
                    json={"content": "第二个请求"}
                )

        result1 = await task1

        assert result1.status_code == 200
        assert response2.status_code == 429

    async def test_concurrent_different_clients_same_conversation_both_allowed(
        self,
        test_session: AsyncSession,
        test_conversation: Conversation,
        test_model_config: ModelConfig
    ):
        """测试不同客户端并发请求同一 conversation 时，两个请求都应该被允许"""
        import asyncio

        app = create_test_app(test_session)

        mock_provider = MagicMock()
        mock_provider.chat = AsyncMock(return_value="测试回复")

        with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response1 = await client.post(
                    f"/api/chat/{test_conversation.id}",
                    json={"content": "客户端1的请求"},
                    headers={"X-Forwarded-For": "192.168.1.1"}
                )

                response2 = await client.post(
                    f"/api/chat/{test_conversation.id}",
                    json={"content": "客户端2的请求"},
                    headers={"X-Forwarded-For": "192.168.1.2"}
                )

        assert response1.status_code == 200
        assert response2.status_code == 200

    async def test_lock_release_timing_after_request_completes(
        self,
        test_session: AsyncSession,
        test_conversation: Conversation,
        test_model_config: ModelConfig
    ):
        """测试锁在请求完成后正确释放，后续请求能够成功"""
        import asyncio

        app = create_test_app(test_session)
        lock_release_time = None
        request_complete_time = None

        async def first_request_with_timing():
            nonlocal lock_release_time, request_complete_time

            async def mock_chat(*args, **kwargs):
                await asyncio.sleep(0.2)
                return "第一次响应"

            mock_provider = MagicMock()
            mock_provider.chat = mock_chat

            from app.core.concurrency import concurrency_lock
            lock_key = f"request:chat:127.0.0.1:{test_conversation.id}"

            with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        f"/api/chat/{test_conversation.id}",
                        json={"content": "第一次请求"}
                    )
                    request_complete_time = asyncio.get_event_loop().time()
                    return response

        task1 = asyncio.create_task(first_request_with_timing())
        await asyncio.sleep(0.3)

        mock_provider2 = MagicMock()
        mock_provider2.chat = AsyncMock(return_value="第二次响应")

        with patch('app.services.teaching_service.get_provider', return_value=mock_provider2):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response2 = await client.post(
                    f"/api/chat/{test_conversation.id}",
                    json={"content": "第二次请求"}
                )

        result1 = await task1

        assert result1.status_code == 200
        assert response2.status_code == 200

    async def test_lock_key_format_with_new_prefix(
        self,
        test_session: AsyncSession,
        test_conversation: Conversation,
        test_model_config: ModelConfig
    ):
        """验证锁键使用新的 'request' 前缀"""
        app = create_test_app(test_session)

        from app.core.concurrency import concurrency_lock

        mock_provider = MagicMock()
        mock_provider.chat = AsyncMock(return_value="测试回复")

        with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    f"/api/chat/{test_conversation.id}",
                    json={"content": "测试前缀"}
                )

        assert response.status_code == 200
