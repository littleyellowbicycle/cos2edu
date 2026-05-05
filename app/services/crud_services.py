from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.core.database import Character, Material, Conversation, Message, ModelConfig
from app.schemas import (
    CharacterCreate, CharacterUpdate,
    MaterialCreate, MaterialUpdate,
    ConversationCreate, ConversationUpdate,
    MessageCreate,
    ModelConfigCreate, ModelConfigUpdate
)
from app.services.llm_providers import get_provider


class CharacterService:
    @staticmethod
    def get_all(db: Session) -> List[Character]:
        return db.query(Character).filter(Character.is_active == True).all()

    @staticmethod
    def get_by_id(db: Session, character_id: int) -> Optional[Character]:
        return db.query(Character).filter(Character.id == character_id).first()

    @staticmethod
    def create(db: Session, character: CharacterCreate) -> Character:
        db_character = Character(
            name=character.name,
            description=character.description,
            personality=character.personality,
            background=character.background,
            avatar=character.avatar,
            avatar_type=character.avatar_type
        )
        db.add(db_character)
        db.commit()
        db.refresh(db_character)
        return db_character

    @staticmethod
    def update(db: Session, character_id: int, character: CharacterUpdate) -> Optional[Character]:
        db_character = CharacterService.get_by_id(db, character_id)
        if db_character:
            update_data = character.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_character, key, value)
            db.commit()
            db.refresh(db_character)
        return db_character

    @staticmethod
    def delete(db: Session, character_id: int) -> bool:
        db_character = CharacterService.get_by_id(db, character_id)
        if db_character:
            db_character.is_active = False
            db.commit()
            return True
        return False


class MaterialService:
    @staticmethod
    def get_all(db: Session) -> List[Material]:
        return db.query(Material).all()

    @staticmethod
    def get_by_id(db: Session, material_id: int) -> Optional[Material]:
        return db.query(Material).filter(Material.id == material_id).first()

    @staticmethod
    def create(db: Session, material: MaterialCreate) -> Material:
        db_material = Material(
            title=material.title,
            description=material.description,
            content=material.content
        )
        db.add(db_material)
        db.commit()
        db.refresh(db_material)
        return db_material

    @staticmethod
    def update(db: Session, material_id: int, material: MaterialUpdate) -> Optional[Material]:
        db_material = MaterialService.get_by_id(db, material_id)
        if db_material:
            update_data = material.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_material, key, value)
            db.commit()
            db.refresh(db_material)
        return db_material

    @staticmethod
    def delete(db: Session, material_id: int) -> bool:
        db_material = MaterialService.get_by_id(db, material_id)
        if db_material:
            db.delete(db_material)
            db.commit()
            return True
        return False


class ConversationService:
    @staticmethod
    def get_all(db: Session) -> List[Conversation]:
        return db.query(Conversation).order_by(Conversation.updated_at.desc()).all()

    @staticmethod
    def get_by_id(db: Session, conversation_id: int) -> Optional[Conversation]:
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()

    @staticmethod
    def create(db: Session, conversation: ConversationCreate) -> Conversation:
        db_conversation = Conversation(
            title=conversation.title,
            character_id=conversation.character_id,
            material_id=conversation.material_id,
            teaching_mode=conversation.teaching_mode
        )
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        return db_conversation

    @staticmethod
    def update(db: Session, conversation_id: int, conversation: ConversationUpdate) -> Optional[Conversation]:
        db_conversation = ConversationService.get_by_id(db, conversation_id)
        if db_conversation:
            update_data = conversation.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_conversation, key, value)
            db.commit()
            db.refresh(db_conversation)
        return db_conversation

    @staticmethod
    def delete(db: Session, conversation_id: int) -> bool:
        db_conversation = ConversationService.get_by_id(db, conversation_id)
        if db_conversation:
            db.query(Message).filter(Message.conversation_id == conversation_id).delete()
            db.delete(db_conversation)
            db.commit()
            return True
        return False


class MessageService:
    @staticmethod
    def get_by_conversation(db: Session, conversation_id: int) -> List[Message]:
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()

    @staticmethod
    def create(db: Session, conversation_id: int, message: MessageCreate) -> Message:
        db_message = Message(
            conversation_id=conversation_id,
            role=message.role,
            content=message.content
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message


class ModelConfigService:
    @staticmethod
    def get_all(db: Session) -> List[ModelConfig]:
        return db.query(ModelConfig).filter(ModelConfig.is_active == True).all()

    @staticmethod
    def get_by_id(db: Session, config_id: int) -> Optional[ModelConfig]:
        return db.query(ModelConfig).filter(ModelConfig.id == config_id).first()

    @staticmethod
    def get_default(db: Session) -> Optional[ModelConfig]:
        return db.query(ModelConfig).filter(
            ModelConfig.is_default == True,
            ModelConfig.is_active == True
        ).first()

    @staticmethod
    def create(db: Session, config: ModelConfigCreate) -> ModelConfig:
        try:
            # 如果是第一个配置，自动设为默认
            existing_count = db.query(ModelConfig).count()
            is_default = config.is_default or existing_count == 0
            
            if is_default:
                db.query(ModelConfig).update({"is_default": False})
                db.flush()
            
            db_config = ModelConfig(
                provider=config.provider,
                model_name=config.model_name,
                api_key=config.api_key,
                base_url=config.base_url,
                is_default=is_default,
                is_active=True
            )
            db.add(db_config)
            db.commit()
            db.refresh(db_config)
            return db_config
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def update(db: Session, config_id: int, config: ModelConfigUpdate) -> Optional[ModelConfig]:
        try:
            db_config = ModelConfigService.get_by_id(db, config_id)
            if db_config:
                if config.is_default:
                    db.query(ModelConfig).filter(ModelConfig.id != config_id).update({"is_default": False})
                    db.flush()
                
                update_data = config.model_dump(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(db_config, key, value)
                db.commit()
                db.refresh(db_config)
            return db_config
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def delete(db: Session, config_id: int) -> bool:
        db_config = ModelConfigService.get_by_id(db, config_id)
        if db_config:
            db_config.is_active = False
            db.commit()
            return True
        return False


class BackgroundConfigService:
    @staticmethod
    def get_all(db: Session) -> List:
        from app.core.database import BackgroundConfig
        return db.query(BackgroundConfig).all()

    @staticmethod
    def get_by_id(db: Session, config_id: int) -> Optional:
        from app.core.database import BackgroundConfig
        return db.query(BackgroundConfig).filter(BackgroundConfig.id == config_id).first()

    @staticmethod
    def get_default(db: Session) -> Optional:
        from app.core.database import BackgroundConfig
        return db.query(BackgroundConfig).filter(
            BackgroundConfig.is_default == True,
            BackgroundConfig.is_active == True
        ).first()

    @staticmethod
    def create(db: Session, config) -> any:
        from app.core.database import BackgroundConfig
        try:
            if config.is_default:
                db.query(BackgroundConfig).update({"is_default": False})
                db.flush()
            
            db_config = BackgroundConfig(
                name=config.name,
                background_type=config.background_type,
                background_value=config.background_value,
                is_default=config.is_default,
                is_active=True
            )
            db.add(db_config)
            db.commit()
            db.refresh(db_config)
            return db_config
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def update(db: Session, config_id: int, config) -> Optional:
        from app.core.database import BackgroundConfig
        try:
            db_config = BackgroundConfigService.get_by_id(db, config_id)
            if db_config:
                if config.is_default:
                    db.query(BackgroundConfig).filter(BackgroundConfig.id != config_id).update({"is_default": False})
                    db.flush()
                
                update_data = config.model_dump(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(db_config, key, value)
                db.commit()
                db.refresh(db_config)
            return db_config
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def delete(db: Session, config_id: int) -> bool:
        from app.core.database import BackgroundConfig
        db_config = BackgroundConfigService.get_by_id(db, config_id)
        if db_config:
            db.delete(db_config)
            db.commit()
            return True
        return False
