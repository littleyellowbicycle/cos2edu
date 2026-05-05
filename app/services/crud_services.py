from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from datetime import datetime

from app.core.database import Character, Material, Conversation, Message, ModelConfig, BackgroundConfig
from app.core.logging_config import get_logger
from app.schemas import (
    CharacterCreate, CharacterUpdate,
    MaterialCreate, MaterialUpdate,
    ConversationCreate, ConversationUpdate,
    MessageCreate,
    ModelConfigCreate, ModelConfigUpdate
)

logger = get_logger(__name__)


class CharacterService:
    @staticmethod
    async def get_all(db: AsyncSession) -> List[Character]:
        result = await db.execute(select(Character).filter(Character.is_active == True))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, character_id: int) -> Optional[Character]:
        result = await db.execute(select(Character).filter(Character.id == character_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[Character]:
        result = await db.execute(select(Character).filter(Character.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, character: CharacterCreate) -> Character:
        db_character = Character(
            name=character.name,
            description=character.description,
            personality=character.personality,
            background=character.background,
            avatar=character.avatar,
            avatar_type=character.avatar_type
        )
        db.add(db_character)
        await db.commit()
        await db.refresh(db_character)
        return db_character

    @staticmethod
    async def update(db: AsyncSession, character_id: int, character: CharacterUpdate) -> Optional[Character]:
        result = await db.execute(select(Character).filter(Character.id == character_id))
        db_character = result.scalar_one_or_none()
        
        if not db_character:
            return None
        
        if character.name is not None:
            db_character.name = character.name
        if character.description is not None:
            db_character.description = character.description
        if character.personality is not None:
            db_character.personality = character.personality
        if character.background is not None:
            db_character.background = character.background
        if character.avatar is not None:
            db_character.avatar = character.avatar
        if character.avatar_type is not None:
            db_character.avatar_type = character.avatar_type
        
        await db.commit()
        await db.refresh(db_character)
        return db_character

    @staticmethod
    async def delete(db: AsyncSession, character_id: int) -> bool:
        result = await db.execute(select(Character).filter(Character.id == character_id))
        db_character = result.scalar_one_or_none()
        
        if not db_character:
            return False
        
        db_character.is_active = False
        await db.commit()
        return True


class MaterialService:
    @staticmethod
    async def get_all(db: AsyncSession) -> List[Material]:
        result = await db.execute(select(Material).order_by(Material.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, material_id: int) -> Optional[Material]:
        result = await db.execute(select(Material).filter(Material.id == material_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, material: MaterialCreate) -> Material:
        db_material = Material(
            title=material.title,
            description=material.description,
            content=material.content
        )
        db.add(db_material)
        await db.commit()
        await db.refresh(db_material)
        return db_material

    @staticmethod
    async def update(db: AsyncSession, material_id: int, material: MaterialUpdate) -> Optional[Material]:
        result = await db.execute(select(Material).filter(Material.id == material_id))
        db_material = result.scalar_one_or_none()
        
        if not db_material:
            return None
        
        if material.title is not None:
            db_material.title = material.title
        if material.description is not None:
            db_material.description = material.description
        if material.content is not None:
            db_material.content = material.content
        
        await db.commit()
        await db.refresh(db_material)
        return db_material

    @staticmethod
    async def delete(db: AsyncSession, material_id: int) -> bool:
        result = await db.execute(delete(Material).filter(Material.id == material_id))
        await db.commit()
        return result.rowcount > 0


class ConversationService:
    @staticmethod
    async def get_all(db: AsyncSession) -> List[Conversation]:
        result = await db.execute(select(Conversation).order_by(Conversation.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, conversation_id: int) -> Optional[Conversation]:
        result = await db.execute(select(Conversation).filter(Conversation.id == conversation_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, conversation: ConversationCreate) -> Conversation:
        db_conversation = Conversation(
            title=conversation.title,
            character_id=conversation.character_id,
            material_id=conversation.material_id,
            teaching_mode=conversation.teaching_mode
        )
        db.add(db_conversation)
        await db.commit()
        await db.refresh(db_conversation)
        return db_conversation

    @staticmethod
    async def update(db: AsyncSession, conversation_id: int, conversation: ConversationUpdate) -> Optional[Conversation]:
        result = await db.execute(select(Conversation).filter(Conversation.id == conversation_id))
        db_conversation = result.scalar_one_or_none()
        
        if not db_conversation:
            return None
        
        if conversation.title is not None:
            db_conversation.title = conversation.title
        if conversation.material_id is not None:
            db_conversation.material_id = conversation.material_id
        if conversation.teaching_mode is not None:
            db_conversation.teaching_mode = conversation.teaching_mode
        
        await db.commit()
        await db.refresh(db_conversation)
        return db_conversation

    @staticmethod
    async def delete(db: AsyncSession, conversation_id: int) -> bool:
        result = await db.execute(delete(Conversation).filter(Conversation.id == conversation_id))
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def save_summary(
        db: AsyncSession,
        conversation_id: int,
        summary: str,
        covered_message_count: int
    ) -> None:
        result = await db.execute(select(Conversation).filter(Conversation.id == conversation_id))
        db_conversation = result.scalar_one_or_none()
        
        if db_conversation:
            db_conversation.summary = summary
            db_conversation.summary_covered_message_count = covered_message_count
            db_conversation.summary_updated_at = datetime.utcnow()
            if not db_conversation.summary_created_at:
                db_conversation.summary_created_at = datetime.utcnow()
            await db.commit()


class MessageService:
    @staticmethod
    async def get_by_conversation(db: AsyncSession, conversation_id: int) -> List[Message]:
        result = await db.execute(
            select(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at)
        )
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, message_id: int) -> Optional[Message]:
        result = await db.execute(select(Message).filter(Message.id == message_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, conversation_id: int, message: MessageCreate) -> Message:
        db_message = Message(
            conversation_id=conversation_id,
            role=message.role,
            content=message.content
        )
        db.add(db_message)
        await db.commit()
        await db.refresh(db_message)
        return db_message

    @staticmethod
    async def delete(db: AsyncSession, message_id: int) -> bool:
        result = await db.execute(delete(Message).filter(Message.id == message_id))
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def count_by_conversation(db: AsyncSession, conversation_id: int) -> int:
        result = await db.execute(
            select(func.count(Message.id)).filter(Message.conversation_id == conversation_id)
        )
        return result.scalar()


class ModelConfigService:
    @staticmethod
    async def get_all(db: AsyncSession) -> List[ModelConfig]:
        result = await db.execute(select(ModelConfig).filter(ModelConfig.is_active == True))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, config_id: int) -> Optional[ModelConfig]:
        result = await db.execute(select(ModelConfig).filter(ModelConfig.id == config_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_default(db: AsyncSession) -> Optional[ModelConfig]:
        result = await db.execute(
            select(ModelConfig).filter(ModelConfig.is_default == True, ModelConfig.is_active == True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, config: ModelConfigCreate) -> ModelConfig:
        count_result = await db.execute(select(func.count(ModelConfig.id)))
        config_count = count_result.scalar()
        
        is_default = config.is_default
        if not is_default and config_count == 0:
            is_default = True
        
        if is_default:
            await db.execute(
                update(ModelConfig).where(ModelConfig.is_default == True).values(is_default=False)
            )
        
        db_config = ModelConfig(
            provider=config.provider,
            model_name=config.model_name,
            api_key=config.api_key,
            base_url=config.base_url,
            is_default=is_default,
            is_active=True
        )
        db.add(db_config)
        await db.commit()
        await db.refresh(db_config)
        return db_config

    @staticmethod
    async def update(db: AsyncSession, config_id: int, config: ModelConfigUpdate) -> Optional[ModelConfig]:
        result = await db.execute(select(ModelConfig).filter(ModelConfig.id == config_id))
        db_config = result.scalar_one_or_none()
        
        if not db_config:
            return None
        
        if config.provider is not None:
            db_config.provider = config.provider
        if config.model_name is not None:
            db_config.model_name = config.model_name
        if config.api_key is not None:
            db_config.api_key = config.api_key
        if config.base_url is not None:
            db_config.base_url = config.base_url
        if config.is_default is not None:
            if config.is_default:
                await db.execute(
                    update(ModelConfig).where(ModelConfig.is_default == True).values(is_default=False)
                )
            db_config.is_default = config.is_default
        if config.is_active is not None:
            db_config.is_active = config.is_active
        
        await db.commit()
        await db.refresh(db_config)
        return db_config

    @staticmethod
    async def delete(db: AsyncSession, config_id: int) -> bool:
        result = await db.execute(delete(ModelConfig).filter(ModelConfig.id == config_id))
        await db.commit()
        return result.rowcount > 0


class BackgroundConfigService:
    @staticmethod
    async def get_all(db: AsyncSession) -> List[BackgroundConfig]:
        result = await db.execute(select(BackgroundConfig))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, config_id: int) -> Optional[BackgroundConfig]:
        result = await db.execute(select(BackgroundConfig).filter(BackgroundConfig.id == config_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_default(db: AsyncSession) -> Optional[BackgroundConfig]:
        result = await db.execute(
            select(BackgroundConfig).filter(BackgroundConfig.is_default == True, BackgroundConfig.is_active == True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, config: dict) -> BackgroundConfig:
        db_config = BackgroundConfig(
            name=config.get("name", ""),
            background_type=config.get("background_type", "color"),
            background_value=config.get("background_value", ""),
            is_active=config.get("is_active", False),
            is_default=config.get("is_default", False)
        )
        db.add(db_config)
        await db.commit()
        await db.refresh(db_config)
        return db_config

    @staticmethod
    async def update(db: AsyncSession, config_id: int, config: dict) -> Optional[BackgroundConfig]:
        result = await db.execute(select(BackgroundConfig).filter(BackgroundConfig.id == config_id))
        db_config = result.scalar_one_or_none()
        
        if not db_config:
            return None
        
        if "name" in config:
            db_config.name = config["name"]
        if "background_type" in config:
            db_config.background_type = config["background_type"]
        if "background_value" in config:
            db_config.background_value = config["background_value"]
        if "is_active" in config:
            db_config.is_active = config["is_active"]
        if "is_default" in config:
            db_config.is_default = config["is_default"]
        
        await db.commit()
        await db.refresh(db_config)
        return db_config

    @staticmethod
    async def delete(db: AsyncSession, config_id: int) -> bool:
        result = await db.execute(delete(BackgroundConfig).filter(BackgroundConfig.id == config_id))
        await db.commit()
        return result.rowcount > 0
