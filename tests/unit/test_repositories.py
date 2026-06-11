import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from models import Character, Material, Conversation, Message, ModelConfig, BackgroundConfig
from app.repositories.unit_of_work import UnitOfWork
from app.repositories.character_repository import CharacterRepository
from app.repositories.material_repository import MaterialRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository


@pytest.mark.asyncio
class TestCharacterRepository:
    
    async def test_create(self, test_session: AsyncSession):
        repo = CharacterRepository(test_session)
        char = await repo.create({
            "name": "测试角色",
            "description": "测试描述",
            "personality": "温和",
            "is_active": True
        })
        await test_session.commit()
        await test_session.refresh(char)
        assert char.id is not None
        assert char.name == "测试角色"
    
    async def test_get_all(self, test_session: AsyncSession, test_character: Character):
        repo = CharacterRepository(test_session)
        chars = await repo.get_all()
        assert len(chars) >= 1
        assert any(c.name == test_character.name for c in chars)
    
    async def test_get_by_id(self, test_session: AsyncSession, test_character: Character):
        repo = CharacterRepository(test_session)
        char = await repo.get_by_id(test_character.id)
        assert char is not None
        assert char.name == test_character.name
    
    async def test_get_by_id_not_found(self, test_session: AsyncSession):
        repo = CharacterRepository(test_session)
        char = await repo.get_by_id(99999)
        assert char is None
    
    async def test_update(self, test_session: AsyncSession, test_character: Character):
        repo = CharacterRepository(test_session)
        updated = await repo.update(test_character, {"name": "更新后的名字"})
        await test_session.commit()
        await test_session.refresh(test_character)
        assert test_character.name == "更新后的名字"
    
    async def test_delete(self, test_session: AsyncSession, test_character: Character):
        repo = CharacterRepository(test_session)
        char_id = test_character.id
        result = await repo.delete(test_character)
        await test_session.commit()
        assert result is True
        deleted = await repo.get_by_id(char_id)
        assert deleted is None


@pytest.mark.asyncio
class TestMaterialRepository:
    
    async def test_create(self, test_session: AsyncSession):
        repo = MaterialRepository(test_session)
        mat = await repo.create({
            "title": "测试教材",
            "description": "测试描述",
            "content": "测试内容"
        })
        await test_session.commit()
        await test_session.refresh(mat)
        assert mat.id is not None
        assert mat.title == "测试教材"
    
    async def test_get_all(self, test_session: AsyncSession, test_material: Material):
        repo = MaterialRepository(test_session)
        mats = await repo.get_all()
        assert len(mats) >= 1
    
    async def test_get_by_id(self, test_session: AsyncSession, test_material: Material):
        repo = MaterialRepository(test_session)
        mat = await repo.get_by_id(test_material.id)
        assert mat is not None
        assert mat.title == test_material.title
    
    async def test_update(self, test_session: AsyncSession, test_material: Material):
        repo = MaterialRepository(test_session)
        updated = await repo.update(test_material, {"title": "更新后的标题"})
        await test_session.commit()
        await test_session.refresh(test_material)
        assert test_material.title == "更新后的标题"
    
    async def test_get_by_id_not_found(self, test_session: AsyncSession):
        repo = MaterialRepository(test_session)
        mat = await repo.get_by_id(99999)
        assert mat is None


@pytest.mark.asyncio
class TestConversationRepository:
    
    async def test_create(self, test_session: AsyncSession, test_character: Character, test_material: Material):
        repo = ConversationRepository(test_session)
        conv = await repo.create({
            "title": "测试对话",
            "character_id": test_character.id,
            "material_id": test_material.id,
            "teaching_mode": "socratic"
        })
        await test_session.commit()
        await test_session.refresh(conv)
        assert conv.id is not None
        assert conv.title == "测试对话"
    
    async def test_get_all(self, test_session: AsyncSession, test_conversation: Conversation):
        repo = ConversationRepository(test_session)
        convs = await repo.get_all()
        assert len(convs) >= 1
    
    async def test_get_by_id_with_relations(self, test_session: AsyncSession, test_conversation: Conversation):
        repo = ConversationRepository(test_session)
        conv = await repo.get_by_id(test_conversation.id)
        assert conv is not None
        assert conv.character is not None
        assert conv.material is not None
    
    async def test_save_summary(self, test_session: AsyncSession, test_conversation: Conversation):
        repo = ConversationRepository(test_session)
        result = await repo.save_summary(
            test_conversation.id,
            "这是一个摘要",
            10
        )
        await test_session.commit()
        assert result is True
        await test_session.refresh(test_conversation)
        assert test_conversation.summary == "这是一个摘要"
        assert test_conversation.summary_covered_message_count == 10


@pytest.mark.asyncio
class TestMessageRepository:
    
    async def test_create(self, test_session: AsyncSession, test_conversation: Conversation):
        repo = MessageRepository(test_session)
        msg = await repo.create({
            "conversation_id": test_conversation.id,
            "role": "user",
            "content": "测试消息"
        })
        await test_session.commit()
        await test_session.refresh(msg)
        assert msg.id is not None
        assert msg.content == "测试消息"
    
    async def test_get_by_conversation(
        self, 
        test_session: AsyncSession, 
        test_conversation: Conversation,
        test_message: Message
    ):
        repo = MessageRepository(test_session)
        msgs = await repo.get_by_conversation(test_conversation.id)
        assert len(msgs) >= 1
        assert any(m.content == test_message.content for m in msgs)
