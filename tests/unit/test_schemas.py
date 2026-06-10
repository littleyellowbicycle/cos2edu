import pytest
from pydantic import ValidationError

from app.schemas import (
    TeachingMode,
    AvatarType,
    BackgroundType,
    ProviderType,
    CharacterCreate,
    CharacterUpdate,
    CharacterResponse,
    MaterialCreate,
    MaterialUpdate,
    MaterialResponse,
    MessageCreate,
    ConversationCreate,
    ConversationUpdate,
    ModelConfigCreate,
    ModelConfigUpdate,
    BackgroundConfigCreate,
    BackgroundConfigUpdate,
    ChatMessage,
)


class TestEnums:
    
    def test_teaching_mode_values(self):
        assert TeachingMode.SOCRATIC == "socratic"
        assert TeachingMode.EXPLANATION == "explanation"
        assert TeachingMode.MIXED == "mixed"
    
    def test_avatar_type_values(self):
        assert AvatarType.EMOJI == "emoji"
        assert AvatarType.IMAGE == "image"
    
    def test_background_type_values(self):
        assert BackgroundType.COLOR == "color"
        assert BackgroundType.IMAGE == "image"
    
    def test_provider_type_values(self):
        assert ProviderType.OPENAI == "openai"
        assert ProviderType.ANTHROPIC == "anthropic"
        assert ProviderType.DASHSCOPE == "dashscope"
        assert ProviderType.ZHIPU == "zhipu"


class TestCharacterSchemas:
    
    def test_character_create_valid(self):
        data = CharacterCreate(
            name="苏格拉底",
            description="古希腊哲学家",
            personality="善于提问"
        )
        assert data.name == "苏格拉底"
        assert data.description == "古希腊哲学家"
        assert data.personality == "善于提问"
    
    def test_character_create_minimal(self):
        data = CharacterCreate(name="苏格拉底")
        assert data.name == "苏格拉底"
        assert data.description is None
        assert data.personality == "善良且乐于助人"
    
    def test_character_create_empty_name_fails(self):
        with pytest.raises(ValidationError):
            CharacterCreate(name="")
    
    def test_character_update_partial(self):
        data = CharacterUpdate(description="新描述")
        assert data.description == "新描述"
        assert data.name is None


class TestMaterialSchemas:
    
    def test_material_create_valid(self):
        data = MaterialCreate(
            title="Python教程",
            description="Python入门",
            content="Python是一种编程语言"
        )
        assert data.title == "Python教程"
        assert data.content == "Python是一种编程语言"
    
    def test_material_create_minimal(self):
        data = MaterialCreate(title="Python教程")
        assert data.title == "Python教程"
        assert data.content is None
    
    def test_material_create_empty_title_fails(self):
        with pytest.raises(ValidationError):
            MaterialCreate(title="")


class TestConversationSchemas:
    
    def test_conversation_create_valid(self):
        data = ConversationCreate(
            character_id=1,
            title="新对话",
            material_id=1,
            teaching_mode="socratic"
        )
        assert data.character_id == 1
        assert data.title == "新对话"
        assert data.teaching_mode == "socratic"
    
    def test_conversation_create_invalid_mode(self):
        with pytest.raises(ValidationError):
            ConversationCreate(character_id=1, teaching_mode="invalid_mode")
    
    def test_conversation_update_material(self):
        data = ConversationUpdate(material_id=2)
        assert data.material_id == 2


class TestMessageSchemas:
    
    def test_message_create_valid(self):
        data = MessageCreate(role="user", content="你好")
        assert data.role == "user"
        assert data.content == "你好"
    
    def test_message_create_invalid_role(self):
        with pytest.raises(ValidationError):
            MessageCreate(role="invalid", content="你好")
    
    def test_message_create_empty_content_fails(self):
        with pytest.raises(ValidationError):
            MessageCreate(role="user", content="")
    
    def test_message_tool_role(self):
        data = MessageCreate(role="tool", content="function result")
        assert data.role == "tool"
    
    def test_message_function_role(self):
        data = MessageCreate(role="function", content="call result")
        assert data.role == "function"
    
    def test_message_system_role(self):
        data = MessageCreate(role="system", content="You are a tutor")
        assert data.role == "system"
    
    def test_message_assistant_role(self):
        data = MessageCreate(role="assistant", content="Let me explain")
        assert data.role == "assistant"


class TestModelConfigSchemas:
    
    def test_model_config_create_valid(self):
        data = ModelConfigCreate(
            provider="openai",
            model_name="gpt-4",
            api_key="sk-test"
        )
        assert data.provider == "openai"
        assert data.model_name == "gpt-4"
    
    def test_model_config_create_with_base_url(self):
        data = ModelConfigCreate(
            provider="openai",
            model_name="gpt-4",
            api_key="sk-test",
            base_url="https://api.openai.com/v1"
        )
        assert data.base_url == "https://api.openai.com/v1"
    
    def test_model_config_invalid_base_url(self):
        with pytest.raises(ValidationError):
            ModelConfigCreate(
                provider="openai",
                model_name="gpt-4",
                base_url="invalid-url"
            )
    
    def test_model_config_empty_provider_fails(self):
        with pytest.raises(ValidationError):
            ModelConfigCreate(provider="", model_name="gpt-4")


class TestChatMessage:
    
    def test_chat_message_valid(self):
        data = ChatMessage(content="你好，苏格拉底")
        assert data.content == "你好，苏格拉底"
    
    def test_chat_message_empty_fails(self):
        with pytest.raises(ValidationError):
            ChatMessage(content="")
