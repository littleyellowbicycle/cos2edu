import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Character, Material, Conversation, Message, ModelConfig
from app.schemas import (
    CharacterCreate, CharacterUpdate,
    MaterialCreate, MaterialUpdate,
    ConversationCreate, ConversationUpdate,
    MessageCreate,
    ModelConfigCreate, ModelConfigUpdate
)
from app.services.crud_services import (
    CharacterService,
    MaterialService,
    ConversationService,
    MessageService,
    ModelConfigService
)


@pytest.mark.asyncio
class TestCharacterService:
    
    async def test_get_all(self, test_session: AsyncSession, test_character: Character):
        characters = await CharacterService.get_all(test_session)
        assert len(characters) == 1
        assert characters[0].name == test_character.name
    
    async def test_get_by_id(self, test_session: AsyncSession, test_character: Character):
        character = await CharacterService.get_by_id(test_session, test_character.id)
        assert character is not None
        assert character.id == test_character.id
    
    async def test_get_by_id_not_found(self, test_session: AsyncSession):
        character = await CharacterService.get_by_id(test_session, 999)
        assert character is None
    
    async def test_create(self, test_session: AsyncSession):
        character_data = CharacterCreate(
            name="新角色",
            description="新角色描述",
            personality="温和、耐心",
            background="测试背景",
            avatar="😊",
            avatar_type="emoji"
        )
        
        character = await CharacterService.create(test_session, character_data)
        
        assert character.id is not None
        assert character.name == "新角色"
        assert character.is_active is True
    
    async def test_update(self, test_session: AsyncSession, test_character: Character):
        update_data = CharacterUpdate(
            name="更新后的角色名",
            description="更新后的描述"
        )
        
        updated = await CharacterService.update(
            test_session, 
            test_character.id, 
            update_data
        )
        
        assert updated.name == "更新后的角色名"
        assert updated.description == "更新后的描述"
    
    async def test_update_not_found(self, test_session: AsyncSession):
        update_data = CharacterUpdate(name="测试")
        updated = await CharacterService.update(test_session, 999, update_data)
        assert updated is None
    
    async def test_delete(self, test_session: AsyncSession, test_character: Character):
        result = await CharacterService.delete(test_session, test_character.id)
        
        assert result is True
        
        # 验证已删除（is_active=False）
        from sqlalchemy import select
        db_character = await test_session.execute(
            select(Character).filter(Character.id == test_character.id)
        )
        character = db_character.scalar_one_or_none()
        assert character is not None
        assert character.is_active is False
    
    async def test_delete_not_found(self, test_session: AsyncSession):
        result = await CharacterService.delete(test_session, 999)
        assert result is False


@pytest.mark.asyncio
class TestMaterialService:
    
    async def test_get_all(self, test_session: AsyncSession, test_material: Material):
        materials = await MaterialService.get_all(test_session)
        assert len(materials) == 1
        assert materials[0].title == test_material.title
    
    async def test_get_by_id(self, test_session: AsyncSession, test_material: Material):
        material = await MaterialService.get_by_id(test_session, test_material.id)
        assert material is not None
        assert material.id == test_material.id
    
    async def test_get_by_id_not_found(self, test_session: AsyncSession):
        material = await MaterialService.get_by_id(test_session, 999)
        assert material is None
    
    async def test_create(self, test_session: AsyncSession):
        material_data = MaterialCreate(
            title="新教材",
            description="新教材描述",
            content="新教材内容"
        )
        
        material = await MaterialService.create(test_session, material_data)
        
        assert material.id is not None
        assert material.title == "新教材"
    
    async def test_update(self, test_session: AsyncSession, test_material: Material):
        update_data = MaterialUpdate(
            title="更新后的教材名",
            content="更新后的内容"
        )
        
        updated = await MaterialService.update(
            test_session,
            test_material.id,
            update_data
        )
        
        assert updated.title == "更新后的教材名"
        assert updated.content == "更新后的内容"
    
    async def test_delete(self, test_session: AsyncSession, test_material: Material):
        result = await MaterialService.delete(test_session, test_material.id)
        
        assert result is True
        
        material = await MaterialService.get_by_id(test_session, test_material.id)
        assert material is None


@pytest.mark.asyncio
class TestConversationService:
    
    async def test_get_all(
        self, 
        test_session: AsyncSession, 
        test_conversation: Conversation
    ):
        conversations = await ConversationService.get_all(test_session)
        assert len(conversations) == 1
        assert conversations[0].id == test_conversation.id
    
    async def test_get_by_id(
        self, 
        test_session: AsyncSession, 
        test_conversation: Conversation
    ):
        conversation = await ConversationService.get_by_id(
            test_session, 
            test_conversation.id
        )
        assert conversation is not None
        assert conversation.id == test_conversation.id
    
    async def test_create(
        self, 
        test_session: AsyncSession, 
        test_character: Character,
        test_material: Material
    ):
        conversation_data = ConversationCreate(
            title="新对话",
            character_id=test_character.id,
            material_id=test_material.id,
            teaching_mode="socratic"
        )
        
        conversation = await ConversationService.create(test_session, conversation_data)
        
        assert conversation.id is not None
        assert conversation.title == "新对话"
    
    async def test_update(
        self, 
        test_session: AsyncSession, 
        test_conversation: Conversation
    ):
        update_data = ConversationUpdate(
            title="更新后的对话标题",
            teaching_mode="explanation"
        )
        
        updated = await ConversationService.update(
            test_session,
            test_conversation.id,
            update_data
        )
        
        assert updated.title == "更新后的对话标题"
        assert updated.teaching_mode == "explanation"
    
    async def test_delete_with_messages(
        self, 
        test_session: AsyncSession, 
        test_conversation: Conversation,
        test_messages: list[Message]
    ):
        conversation_id = test_conversation.id
        
        result = await ConversationService.delete(test_session, conversation_id)
        
        assert result is True
        
        conversation = await ConversationService.get_by_id(test_session, conversation_id)
        assert conversation is None


@pytest.mark.asyncio
class TestMessageService:
    
    async def test_get_by_conversation(
        self, 
        test_session: AsyncSession, 
        test_conversation: Conversation,
        test_messages: list[Message]
    ):
        messages = await MessageService.get_by_conversation(
            test_session, 
            test_conversation.id
        )
        
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
    
    async def test_get_by_conversation_empty(self, test_session: AsyncSession, test_conversation: Conversation):
        messages = await MessageService.get_by_conversation(test_session, test_conversation.id)
        assert len(messages) == 0
    
    async def test_create(self, test_session: AsyncSession, test_conversation: Conversation):
        message_data = MessageCreate(
            role="user",
            content="测试消息内容"
        )
        
        message = await MessageService.create(
            test_session,
            test_conversation.id,
            message_data
        )
        
        assert message.id is not None
        assert message.role == "user"
        assert message.content == "测试消息内容"


@pytest.mark.asyncio
class TestModelConfigService:
    
    async def test_get_all(self, test_session: AsyncSession, test_model_config: ModelConfig):
        configs = await ModelConfigService.get_all(test_session)
        assert len(configs) == 1
        assert configs[0].model_name == test_model_config.model_name
    
    async def test_get_by_id(self, test_session: AsyncSession, test_model_config: ModelConfig):
        config = await ModelConfigService.get_by_id(test_session, test_model_config.id)
        assert config is not None
        assert config.id == test_model_config.id
    
    async def test_get_default(self, test_session: AsyncSession, test_model_config: ModelConfig):
        default = await ModelConfigService.get_default(test_session)
        assert default is not None
        assert default.is_default is True
    
    async def test_get_default_none(self, test_session: AsyncSession):
        default = await ModelConfigService.get_default(test_session)
        assert default is None
    
    async def test_create_first_config_is_default(self, test_session: AsyncSession):
        config_data = ModelConfigCreate(
            provider="anthropic",
            model_name="claude-3",
            api_key="test-key",
            base_url=None
        )
        
        config = await ModelConfigService.create(test_session, config_data)
        
        assert config.is_default is True
    
    async def test_create_resets_existing_default(self, test_session: AsyncSession, test_model_config: ModelConfig):
        config_data = ModelConfigCreate(
            provider="anthropic",
            model_name="claude-3",
            api_key="test-key-2",
            is_default=True
        )
        
        new_config = await ModelConfigService.create(test_session, config_data)
        
        await test_session.refresh(test_model_config)
        
        assert new_config.is_default is True
        assert test_model_config.is_default is False
    
    async def test_update_sets_default(self, test_session: AsyncSession, test_model_config: ModelConfig):
        from sqlalchemy import update
        await test_session.execute(
            update(ModelConfig).values(is_default=False)
        )
        await test_session.commit()
        
        update_data = ModelConfigUpdate(is_default=True)
        
        updated = await ModelConfigService.update(
            test_session,
            test_model_config.id,
            update_data
        )
        
        assert updated.is_default is True
    
    async def test_delete(self, test_session: AsyncSession, test_model_config: ModelConfig):
        result = await ModelConfigService.delete(test_session, test_model_config.id)
        
        assert result is True
        
        config = await ModelConfigService.get_by_id(test_session, test_model_config.id)
        assert config.is_active is False
