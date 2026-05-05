import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Character, Material, Conversation, Message, ModelConfig
from app.services.teaching_service import (
    TeachingService,
    TitleGeneratorService,
    ChatService
)


@pytest.mark.asyncio
class TestTeachingService:
    
    async def test_build_system_prompt_socratic_mode(self, test_character: Character):
        prompt = TeachingService.build_system_prompt(
            character=test_character,
            material=None,
            teaching_mode="socratic"
        )
        
        assert "苏格拉底教学法" in prompt
        assert test_character.personality in prompt
    
    async def test_build_system_prompt_explanation_mode(self, test_character: Character):
        prompt = TeachingService.build_system_prompt(
            character=test_character,
            material=None,
            teaching_mode="explanation"
        )
        
        assert "知识渊博、善于讲解的导师" in prompt
    
    async def test_build_system_prompt_mixed_mode(self, test_character: Character):
        prompt = TeachingService.build_system_prompt(
            character=test_character,
            material=None,
            teaching_mode="mixed"
        )
        
        assert "灵活多变的导师" in prompt
    
    async def test_build_system_prompt_with_background(self, test_character: Character):
        test_character.background = "测试背景故事"
        
        prompt = TeachingService.build_system_prompt(
            character=test_character,
            material=None,
            teaching_mode="socratic"
        )
        
        assert "背景故事" in prompt
        assert "测试背景故事" in prompt
    
    async def test_build_system_prompt_without_background(self, test_character: Character):
        test_character.background = None
        
        prompt = TeachingService.build_system_prompt(
            character=test_character,
            material=None,
            teaching_mode="socratic"
        )
        
        assert "背景故事" not in prompt
    
    async def test_build_system_prompt_with_material(
        self, 
        test_character: Character, 
        test_material: Material
    ):
        test_material.content = "测试教材内容"
        
        prompt = TeachingService.build_system_prompt(
            character=test_character,
            material=test_material,
            teaching_mode="socratic"
        )
        
        assert "当前学习的教材内容" in prompt
        assert "测试教材内容" in prompt
    
    async def test_build_chat_messages(
        self,
        test_session: AsyncSession,
        test_conversation: Conversation,
        test_messages: list[Message]
    ):
        messages = await TeachingService.build_chat_messages(
            db=test_session,
            conversation=test_conversation,
            user_message="新的问题"
        )
        
        assert isinstance(messages, list)
        assert len(messages) > 0
        assert messages[0]["role"] == "system"


@pytest.mark.asyncio
class TestTitleGeneratorService:
    
    async def test_generate_title_no_model_config(self, test_session: AsyncSession):
        title = await TitleGeneratorService.generate_title(
            db=test_session,
            user_message="测试消息",
            model_config=None
        )
        
        assert title is None
    
    async def test_generate_title_with_valid_response(
        self,
        test_session: AsyncSession,
        test_model_config: ModelConfig
    ):
        mock_provider = AsyncMock()
        mock_provider.chat.return_value = "测试对话标题"
        
        with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
            title = await TitleGeneratorService.generate_title(
                db=test_session,
                user_message="用户的第一条消息",
                model_config=test_model_config
            )
        
        assert title == "测试对话标题"
    
    async def test_generate_title_strips_quotes(
        self,
        test_session: AsyncSession,
        test_model_config: ModelConfig
    ):
        mock_provider = AsyncMock()
        mock_provider.chat.return_value = '"带引号的标题"'
        
        with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
            title = await TitleGeneratorService.generate_title(
                db=test_session,
                user_message="用户消息",
                model_config=test_model_config
            )
        
        assert title == "带引号的标题"
    
    async def test_generate_title_exception_handling(
        self,
        test_session: AsyncSession,
        test_model_config: ModelConfig
    ):
        mock_provider = AsyncMock()
        mock_provider.chat.side_effect = Exception("API Error")
        
        with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
            title = await TitleGeneratorService.generate_title(
                db=test_session,
                user_message="用户消息",
                model_config=test_model_config
            )
        
        assert title is None


@pytest.mark.asyncio
class TestChatService:
    
    async def test_chat_non_existent_conversation(self, test_session: AsyncSession):
        with pytest.raises(ValueError) as exc_info:
            await ChatService.chat(
                db=test_session,
                conversation_id=999,
                user_message="测试消息"
            )
        
        assert "对话不存在" in str(exc_info.value)
    
    async def test_chat_no_model_config(
        self,
        test_session: AsyncSession,
        test_conversation: Conversation
    ):
        with pytest.raises(ValueError) as exc_info:
            await ChatService.chat(
                db=test_session,
                conversation_id=test_conversation.id,
                user_message="测试消息"
            )
        
        assert "未配置模型" in str(exc_info.value)
    
    async def test_chat_success(
        self,
        test_session: AsyncSession,
        test_conversation: Conversation,
        test_model_config: ModelConfig
    ):
        mock_provider = AsyncMock()
        mock_provider.chat.return_value = "助手的回复"
        
        with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
            response = await ChatService.chat(
                db=test_session,
                conversation_id=test_conversation.id,
                user_message="用户消息",
                model_config=test_model_config
            )
        
        assert response == "助手的回复"
    
    async def test_chat_first_message_generates_title(
        self,
        test_session: AsyncSession,
        test_conversation: Conversation,
        test_model_config: ModelConfig
    ):
        mock_provider = AsyncMock()
        mock_provider.chat.side_effect = [
            "助手的回复",
            "自动生成的对话标题"
        ]
        
        with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
            await ChatService.chat(
                db=test_session,
                conversation_id=test_conversation.id,
                user_message="用户消息",
                model_config=test_model_config
            )
        
        await test_session.refresh(test_conversation)
        assert test_conversation.title == "自动生成的对话标题"
    
    async def test_chat_stream_non_existent_conversation(self, test_session: AsyncSession):
        with pytest.raises(ValueError) as exc_info:
            async for chunk in ChatService.chat_stream(
                db=test_session,
                conversation_id=999,
                user_message="测试消息"
            ):
                pass
        
        assert "对话不存在" in str(exc_info.value)
    
    async def test_chat_stream_no_model_config(
        self,
        test_session: AsyncSession,
        test_conversation: Conversation
    ):
        with pytest.raises(ValueError) as exc_info:
            async for chunk in ChatService.chat_stream(
                db=test_session,
                conversation_id=test_conversation.id,
                user_message="测试消息"
            ):
                pass
        
        assert "未配置模型" in str(exc_info.value)
    
    async def test_chat_stream_success(
        self,
        test_session: AsyncSession,
        test_conversation: Conversation,
        test_model_config: ModelConfig
    ):
        async def mock_chat_stream(*args, **kwargs):
            for chunk in ["你", "好", "！"]:
                yield chunk
        
        mock_provider = MagicMock()
        mock_provider.chat_stream = mock_chat_stream
        
        with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
            full_response = ""
            async for chunk in ChatService.chat_stream(
                db=test_session,
                conversation_id=test_conversation.id,
                user_message="测试消息",
                model_config=test_model_config
            ):
                full_response += chunk
        
        assert full_response == "你好！"
    
    async def test_chat_stream_exception_rollback(
        self,
        test_session: AsyncSession,
        test_conversation: Conversation,
        test_model_config: ModelConfig
    ):
        from app.core.database import Message
        from sqlalchemy import select, func
        
        result = await test_session.execute(select(func.count(Message.id)))
        initial_messages = result.scalar()
        
        async def mock_chat_stream(*args, **kwargs):
            yield "你"
            raise Exception("Stream Error")
        
        mock_provider = MagicMock()
        mock_provider.chat_stream = mock_chat_stream
        
        with pytest.raises(Exception) as exc_info:
            with patch('app.services.teaching_service.get_provider', return_value=mock_provider):
                async for chunk in ChatService.chat_stream(
                    db=test_session,
                    conversation_id=test_conversation.id,
                    user_message="测试消息",
                    model_config=test_model_config
                ):
                    pass
        
        assert "Stream Error" in str(exc_info.value)
        
        result = await test_session.execute(select(func.count(Message.id)))
        messages_after = result.scalar()
        assert messages_after == initial_messages
