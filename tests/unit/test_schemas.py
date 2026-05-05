import pytest
from pydantic import ValidationError

from app.schemas import (
    TeachingMode,
    AvatarType,
    BackgroundType,
    ProviderType,
    CharacterCreate,
    CharacterUpdate,
    MaterialCreate,
    MaterialUpdate,
    MessageCreate,
    MessageBase,
    ConversationCreate,
    ConversationUpdate,
    ModelConfigCreate,
    ModelConfigUpdate,
    BackgroundConfigCreate,
    BackgroundConfigUpdate
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
        assert ProviderType.CUSTOM == "custom"


class TestCharacterSchemas:
    
    def test_character_create_valid(self):
        data = {
            "name": "测试角色",
            "description": "测试描述",
            "personality": "测试性格",
            "background": "测试背景",
            "avatar": "😊",
            "avatar_type": "emoji"
        }
        
        schema = CharacterCreate(**data)
        assert schema.name == "测试角色"
        assert schema.avatar_type == "emoji"
    
    def test_character_create_required_fields(self):
        with pytest.raises(ValidationError):
            CharacterCreate(description="test")
    
    def test_character_create_invalid_avatar_type(self):
        with pytest.raises(ValidationError) as exc_info:
            CharacterCreate(
                name="测试",
                personality="性格",
                avatar_type="invalid"
            )
        
        assert "无效的头像类型" in str(exc_info.value)
    
    def test_character_avatar_type_lowercase(self):
        data = {
            "name": "测试角色",
            "personality": "测试性格",
            "avatar_type": "EMOJI"
        }
        
        schema = CharacterCreate(**data)
        assert schema.avatar_type == "emoji"
    
    def test_character_update_partial(self):
        data = {
            "name": "更新的名称"
        }
        
        schema = CharacterUpdate(**data)
        assert schema.name == "更新的名称"
        assert schema.personality is None


class TestMaterialSchemas:
    
    def test_material_create_valid(self):
        data = {
            "title": "测试教材",
            "description": "测试描述",
            "content": "测试内容"
        }
        
        schema = MaterialCreate(**data)
        assert schema.title == "测试教材"
    
    def test_material_create_required_fields(self):
        with pytest.raises(ValidationError):
            MaterialCreate(title="test")
    
    def test_material_update_partial(self):
        data = {
            "title": "更新的标题"
        }
        
        schema = MaterialUpdate(**data)
        assert schema.title == "更新的标题"
        assert schema.content is None


class TestMessageSchemas:
    
    def test_message_create_valid(self):
        data = {
            "role": "user",
            "content": "测试消息"
        }
        
        schema = MessageCreate(**data)
        assert schema.role == "user"
        assert schema.content == "测试消息"
    
    def test_message_role_validation_valid(self):
        for role in ["user", "assistant", "system"]:
            schema = MessageBase(role=role, content="test")
            assert schema.role == role
    
    def test_message_role_validation_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            MessageBase(role="invalid", content="test")
        
        assert "无效的消息角色" in str(exc_info.value)
    
    def test_message_role_lowercase(self):
        schema = MessageBase(role="USER", content="test")
        assert schema.role == "user"
    
    def test_message_content_required(self):
        with pytest.raises(ValidationError):
            MessageBase(role="user", content="")


class TestConversationSchemas:
    
    def test_conversation_create_valid(self):
        data = {
            "title": "新对话",
            "character_id": 1,
            "material_id": 2,
            "teaching_mode": "socratic"
        }
        
        schema = ConversationCreate(**data)
        assert schema.teaching_mode == "socratic"
    
    def test_conversation_create_default_mode(self):
        data = {
            "character_id": 1
        }
        
        schema = ConversationCreate(**data)
        assert schema.teaching_mode == "socratic"
    
    def test_conversation_teaching_mode_valid(self):
        for mode in ["socratic", "explanation", "mixed"]:
            schema = ConversationCreate(character_id=1, teaching_mode=mode)
            assert schema.teaching_mode == mode
    
    def test_conversation_teaching_mode_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            ConversationCreate(character_id=1, teaching_mode="invalid")
        
        assert "无效的教学模式" in str(exc_info.value)
    
    def test_conversation_teaching_mode_lowercase(self):
        schema = ConversationCreate(character_id=1, teaching_mode="SOCRATIC")
        assert schema.teaching_mode == "socratic"
    
    def test_conversation_update_partial(self):
        data = {
            "title": "更新的标题"
        }
        
        schema = ConversationUpdate(**data)
        assert schema.title == "更新的标题"
        assert schema.teaching_mode is None


class TestModelConfigSchemas:
    
    def test_model_config_create_valid(self):
        data = {
            "provider": "openai",
            "model_name": "gpt-4",
            "api_key": "test-key",
            "base_url": "https://api.openai.com/v1"
        }
        
        schema = ModelConfigCreate(**data)
        assert schema.provider == "openai"
        assert schema.base_url == "https://api.openai.com/v1"
    
    def test_model_config_provider_required(self):
        with pytest.raises(ValidationError):
            ModelConfigCreate(provider="", model_name="gpt-4")
    
    def test_model_config_provider_lowercase(self):
        schema = ModelConfigCreate(provider="OPENAI", model_name="gpt-4")
        assert schema.provider == "openai"
    
    def test_model_config_base_url_valid(self):
        valid_urls = [
            "https://api.openai.com/v1",
            "http://localhost:8000",
        ]
        
        for url in valid_urls:
            schema = ModelConfigCreate(
                provider="openai",
                model_name="gpt-4",
                base_url=url
            )
            assert schema.base_url == url
    
    def test_model_config_base_url_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            ModelConfigCreate(
                provider="openai",
                model_name="gpt-4",
                base_url="not-a-url"
            )
        
        assert "base_url必须以http://或https://开头" in str(exc_info.value)
    
    def test_model_config_base_url_strips_trailing_slash(self):
        schema = ModelConfigCreate(
            provider="openai",
            model_name="gpt-4",
            base_url="https://api.openai.com/v1/"
        )
        assert schema.base_url == "https://api.openai.com/v1"
    
    def test_model_config_update_partial(self):
        data = {
            "model_name": "gpt-4-turbo"
        }
        
        schema = ModelConfigUpdate(**data)
        assert schema.model_name == "gpt-4-turbo"
        assert schema.provider is None


class TestBackgroundConfigSchemas:
    
    def test_background_config_create_valid(self):
        data = {
            "name": "蓝色背景",
            "background_type": "color",
            "background_value": "#0000ff",
            "is_default": True
        }
        
        schema = BackgroundConfigCreate(**data)
        assert schema.name == "蓝色背景"
        assert schema.background_type == "color"
    
    def test_background_config_type_valid(self):
        for bg_type in ["color", "image"]:
            schema = BackgroundConfigCreate(
                name="test",
                background_type=bg_type,
                background_value="value"
            )
            assert schema.background_type == bg_type
    
    def test_background_config_type_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            BackgroundConfigCreate(
                name="test",
                background_type="invalid",
                background_value="value"
            )
        
        assert "无效的背景类型" in str(exc_info.value)
    
    def test_background_config_type_lowercase(self):
        schema = BackgroundConfigCreate(
            name="test",
            background_type="COLOR",
            background_value="value"
        )
        assert schema.background_type == "color"
    
    def test_background_config_update_partial(self):
        data = {
            "is_default": True
        }
        
        schema = BackgroundConfigUpdate(**data)
        assert schema.is_default is True
        assert schema.name is None
