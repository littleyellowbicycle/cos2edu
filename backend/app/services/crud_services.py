from typing import List, Optional
from models.character import Character
from models.material import Material
from models.conversation import Conversation
from models.message import Message
from models.model_config import ModelConfig
from models.background_config import BackgroundConfig
from app.core.logging_config import get_logger
from app.schemas import (
    CharacterCreate, CharacterUpdate,
    MaterialCreate, MaterialUpdate,
    ConversationCreate, ConversationUpdate,
    MessageCreate,
    ModelConfigCreate, ModelConfigUpdate
)
from ..repositories.unit_of_work import UnitOfWork


logger = get_logger(__name__)


class CharacterService:
    @staticmethod
    async def get_all() -> List[Character]:
        async with UnitOfWork() as uow:
            return await uow.characters.get_all()

    @staticmethod
    async def get_by_id(character_id: int) -> Optional[Character]:
        async with UnitOfWork() as uow:
            return await uow.characters.get_by_id(character_id)

    @staticmethod
    async def create(character: CharacterCreate) -> Character:
        async with UnitOfWork() as uow:
            return await uow.characters.create(character.model_dump())

    @staticmethod
    async def update(character_id: int, character: CharacterUpdate) -> Optional[Character]:
        async with UnitOfWork() as uow:
            db_character = await uow.characters.get_by_id(character_id)
            if not db_character:
                return None
            return await uow.characters.update(db_character, character.model_dump(exclude_unset=True))

    @staticmethod
    async def delete(character_id: int) -> bool:
        async with UnitOfWork() as uow:
            db_character = await uow.characters.get_by_id(character_id)
            if not db_character:
                return False
            db_character.is_active = False
            return True


class MaterialService:
    @staticmethod
    async def get_all() -> List[Material]:
        async with UnitOfWork() as uow:
            return await uow.materials.get_all()

    @staticmethod
    async def get_by_id(material_id: int) -> Optional[Material]:
        async with UnitOfWork() as uow:
            return await uow.materials.get_by_id(material_id)

    @staticmethod
    async def create(material: MaterialCreate) -> Material:
        async with UnitOfWork() as uow:
            data = material.model_dump()
            if data.get('content') is None:
                data['content'] = ''
            return await uow.materials.create(data)

    @staticmethod
    async def update(material_id: int, material: MaterialUpdate) -> Optional[Material]:
        async with UnitOfWork() as uow:
            db_material = await uow.materials.get_by_id(material_id)
            if not db_material:
                return None
            return await uow.materials.update(db_material, material.model_dump(exclude_unset=True))

    @staticmethod
    async def delete(material_id: int) -> bool:
        async with UnitOfWork() as uow:
            db_material = await uow.materials.get_by_id(material_id)
            if not db_material:
                return False
            await uow.materials.delete(db_material)
            return True


class ConversationService:
    @staticmethod
    async def get_all() -> List[Conversation]:
        async with UnitOfWork() as uow:
            return await uow.conversations.get_all()

    @staticmethod
    async def get_by_id(conversation_id: int) -> Optional[Conversation]:
        async with UnitOfWork() as uow:
            return await uow.conversations.get_by_id(conversation_id)

    @staticmethod
    async def create(conversation: ConversationCreate) -> Conversation:
        async with UnitOfWork() as uow:
            return await uow.conversations.create(conversation.model_dump())

    @staticmethod
    async def update(conversation_id: int, conversation: ConversationUpdate) -> Optional[Conversation]:
        async with UnitOfWork() as uow:
            db_conversation = await uow.conversations.get_by_id(conversation_id)
            if not db_conversation:
                return None
            return await uow.conversations.update(db_conversation, conversation.model_dump(exclude_unset=True))

    @staticmethod
    async def delete(conversation_id: int) -> bool:
        async with UnitOfWork() as uow:
            return await uow.conversations.delete_with_messages(conversation_id)

    @staticmethod
    async def save_summary(
        conversation_id: int,
        summary: str,
        covered_message_count: int
    ) -> bool:
        async with UnitOfWork() as uow:
            success = await uow.conversations.save_summary(
                conversation_id, summary, covered_message_count
            )
            if success:
                logger.info(
                    f"对话摘要已保存: conversation_id={conversation_id}, "
                    f"covered_message_count={covered_message_count}, "
                    f"summary_length={len(summary)}"
                )
            return success

    @staticmethod
    async def clear_summary(conversation_id: int) -> bool:
        async with UnitOfWork() as uow:
            success = await uow.conversations.clear_summary(conversation_id)
            if success:
                logger.info(f"对话摘要已清除: conversation_id={conversation_id}")
            return success


class MessageService:
    @staticmethod
    async def get_by_conversation(conversation_id: int) -> List[Message]:
        async with UnitOfWork() as uow:
            return await uow.messages.get_by_conversation(conversation_id)

    @staticmethod
    async def create(conversation_id: int, message: MessageCreate) -> Message:
        async with UnitOfWork() as uow:
            return await uow.messages.create({
                "conversation_id": conversation_id,
                "role": message.role,
                "content": message.content
            })


class ModelConfigService:
    @staticmethod
    async def get_all() -> List[ModelConfig]:
        async with UnitOfWork() as uow:
            return await uow.model_configs.get_all()

    @staticmethod
    async def get_by_id(config_id: int) -> Optional[ModelConfig]:
        async with UnitOfWork() as uow:
            return await uow.model_configs.get_by_id(config_id)

    @staticmethod
    async def get_default() -> Optional[ModelConfig]:
        async with UnitOfWork() as uow:
            return await uow.model_configs.get_default()

    @staticmethod
    async def create(config: ModelConfigCreate) -> ModelConfig:
        async with UnitOfWork() as uow:
            return await uow.model_configs.create(config.model_dump())

    @staticmethod
    async def update(config_id: int, config: ModelConfigUpdate) -> Optional[ModelConfig]:
        async with UnitOfWork() as uow:
            db_config = await uow.model_configs.get_by_id(config_id)
            if not db_config:
                return None
            return await uow.model_configs.update(db_config, config.model_dump(exclude_unset=True))

    @staticmethod
    async def delete(config_id: int) -> bool:
        async with UnitOfWork() as uow:
            db_config = await uow.model_configs.get_by_id(config_id)
            if not db_config:
                return False
            await uow.model_configs.delete(db_config)
            return True


class BackgroundConfigService:
    @staticmethod
    async def get_all() -> List[BackgroundConfig]:
        async with UnitOfWork() as uow:
            return await uow.background_configs.get_all()

    @staticmethod
    async def get_by_id(config_id: int) -> Optional[BackgroundConfig]:
        async with UnitOfWork() as uow:
            return await uow.background_configs.get_by_id(config_id)

    @staticmethod
    async def get_default() -> Optional[BackgroundConfig]:
        async with UnitOfWork() as uow:
            return await uow.background_configs.get_default()

    @staticmethod
    async def create(config) -> BackgroundConfig:
        async with UnitOfWork() as uow:
            return await uow.background_configs.create({
                "name": config.name,
                "background_type": config.background_type,
                "background_value": config.background_value,
                "is_default": config.is_default
            })

    @staticmethod
    async def update(config_id: int, config) -> Optional[BackgroundConfig]:
        async with UnitOfWork() as uow:
            db_config = await uow.background_configs.get_by_id(config_id)
            if not db_config:
                return None
            return await uow.background_configs.update(db_config, config.model_dump(exclude_unset=True))

    @staticmethod
    async def delete(config_id: int) -> bool:
        async with UnitOfWork() as uow:
            db_config = await uow.background_configs.get_by_id(config_id)
            if not db_config:
                return False
            await uow.background_configs.delete(db_config)
            return True