from typing import List, Dict, Optional, AsyncIterator
from sqlalchemy.orm import Session
from app.core.database import Conversation, Character, Material, ModelConfig, Message
from app.schemas import MessageCreate
from app.services.crud_services import MessageService, ModelConfigService
from app.services.llm_providers import get_provider


class TeachingService:
    SOCRATIC_PROMPT = """你是一位精通苏格拉底教学法的导师。苏格拉底教学法的核心是：
1. 不直接给出答案，而是通过精心设计的问题引导学生自己思考
2. 从学生已知的知识出发，逐步引导到新的知识
3. 鼓励学生质疑、推理、验证
4. 当学生犯错时，通过反问让他们自己发现错误

请始终遵循以下规则：
- 绝对不要直接给出答案或完整的解释
- 每次用1-2个引导性问题来推进学习
- 问题要循序渐进，从简单到复杂
- 密切关注学生的回答，根据他们的理解程度调整问题
- 保持耐心和鼓励的态度
- 当学生得出正确结论时，给予肯定并提出下一个更深层次的问题

你的性格设定：
{personality}

{background}

请用中文与学生交流。"""

    EXPLANATION_PROMPT = """你是一位知识渊博、善于讲解的导师。你的教学风格是：
1. 用通俗易懂的语言解释复杂概念
2. 多举例子帮助理解
3. 结构清晰，逻辑严谨
4. 鼓励学生提问

你的性格设定：
{personality}

{background}

请用中文与学生交流。"""

    MIXED_PROMPT = """你是一位灵活多变的导师。你会根据学习内容和学生的情况，灵活运用苏格拉底式提问和直接讲解：
- 对于新概念和需要深度理解的内容，使用苏格拉底式提问引导
- 对于需要快速了解的背景知识，可以直接讲解
- 保持互动，关注学生的反馈

你的性格设定：
{personality}

{background}

请用中文与学生交流。"""

    @staticmethod
    def build_system_prompt(
        character: Character,
        material: Optional[Material],
        teaching_mode: str
    ) -> str:
        personality = character.personality
        background = character.background or ""
        
        if teaching_mode == "socratic":
            base_prompt = TeachingService.SOCRATIC_PROMPT
        elif teaching_mode == "explanation":
            base_prompt = TeachingService.EXPLANATION_PROMPT
        else:
            base_prompt = TeachingService.MIXED_PROMPT
        
        system_prompt = base_prompt.format(
            personality=personality,
            background=f"背景故事：{background}" if background else ""
        )
        
        if material:
            material_context = f"\n\n当前学习的教材内容：\n{material.content}\n"
            system_prompt += material_context
        
        return system_prompt

    @staticmethod
    def build_chat_messages(
        db: Session,
        conversation: Conversation,
        user_message: str
    ) -> List[Dict[str, str]]:
        character = conversation.character
        material = conversation.material
        teaching_mode = conversation.teaching_mode
        
        system_prompt = TeachingService.build_system_prompt(
            character, material, teaching_mode
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        
        history_messages = MessageService.get_by_conversation(db, conversation.id)
        for msg in history_messages:
            messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": user_message})
        
        return messages


class TitleGeneratorService:
    TITLE_GENERATION_PROMPT = """你是一个对话标题生成器。根据用户的第一条消息，生成一个简洁、有意义的对话标题。

规则：
1. 标题应该简洁（10-20字最佳，最多30字）
2. 标题应该准确概括对话主题
3. 不要使用问句形式
4. 直接输出标题，不要加引号或其他装饰

用户消息：
{message}

请生成标题："""

    @staticmethod
    async def generate_title(
        db: Session,
        user_message: str,
        model_config: Optional[ModelConfig] = None
    ) -> Optional[str]:
        if not model_config:
            model_config = ModelConfigService.get_default(db)
            if not model_config:
                return None
        
        try:
            messages = [{
                "role": "user",
                "content": TitleGeneratorService.TITLE_GENERATION_PROMPT.format(message=user_message)
            }]
            
            provider = get_provider(
                provider_name=model_config.provider,
                api_key=model_config.api_key,
                base_url=model_config.base_url
            )
            
            title = await provider.chat(
                messages=messages,
                model=model_config.model_name,
                temperature=0.3,
                max_tokens=50
            )
            
            title = title.strip().strip('"').strip("'").strip()
            
            if title and len(title) > 0 and len(title) <= 50:
                return title
            return None
        except Exception as e:
            print(f"生成标题失败: {e}")
            return None


class ChatService:
    @staticmethod
    async def chat(
        db: Session,
        conversation_id: int,
        user_message: str,
        model_config: Optional[ModelConfig] = None
    ) -> str:
        from app.services.crud_services import ConversationService
        
        conversation = ConversationService.get_by_id(db, conversation_id)
        if not conversation:
            raise ValueError(f"对话不存在: {conversation_id}")
        
        if not model_config:
            model_config = ModelConfigService.get_default(db)
            if not model_config:
                raise ValueError("未配置模型，请先在设置中配置模型")
        
        existing_messages = MessageService.get_by_conversation(db, conversation_id)
        is_first_message = len(existing_messages) == 0
        
        MessageService.create(db, conversation_id, MessageCreate(
            role="user",
            content=user_message
        ))
        
        messages = TeachingService.build_chat_messages(db, conversation, user_message)
        
        provider = get_provider(
            provider_name=model_config.provider,
            api_key=model_config.api_key,
            base_url=model_config.base_url
        )
        
        response = await provider.chat(
            messages=messages,
            model=model_config.model_name,
            temperature=0.7,
            max_tokens=2000
        )
        
        MessageService.create(db, conversation_id, MessageCreate(
            role="assistant",
            content=response
        ))
        
        if is_first_message and (not conversation.title or conversation.title == "新对话"):
            generated_title = await TitleGeneratorService.generate_title(
                db=db,
                user_message=user_message,
                model_config=model_config
            )
            if generated_title:
                from app.schemas import ConversationUpdate
                ConversationService.update(
                    db=db,
                    conversation_id=conversation_id,
                    conversation=ConversationUpdate(title=generated_title)
                )
        
        return response

    @staticmethod
    async def chat_stream(
        db: Session,
        conversation_id: int,
        user_message: str,
        model_config: Optional[ModelConfig] = None
    ) -> AsyncIterator[str]:
        from app.services.crud_services import ConversationService
        
        conversation = ConversationService.get_by_id(db, conversation_id)
        if not conversation:
            raise ValueError(f"对话不存在: {conversation_id}")
        
        if not model_config:
            model_config = ModelConfigService.get_default(db)
            if not model_config:
                raise ValueError("未配置模型，请先在设置中配置模型")
        
        existing_messages = MessageService.get_by_conversation(db, conversation_id)
        is_first_message = len(existing_messages) == 0
        
        user_message_id = None
        try:
            db_user_message = MessageService.create(db, conversation_id, MessageCreate(
                role="user",
                content=user_message
            ))
            user_message_id = db_user_message.id
            
            messages = TeachingService.build_chat_messages(db, conversation, user_message)
            
            provider = get_provider(
                provider_name=model_config.provider,
                api_key=model_config.api_key,
                base_url=model_config.base_url
            )
            
            full_response = ""
            async for chunk in provider.chat_stream(
                messages=messages,
                model=model_config.model_name,
                temperature=0.7,
                max_tokens=2000
            ):
                full_response += chunk
                yield chunk
            
            MessageService.create(db, conversation_id, MessageCreate(
                role="assistant",
                content=full_response
            ))
            
            if is_first_message and (not conversation.title or conversation.title == "新对话"):
                generated_title = await TitleGeneratorService.generate_title(
                    db=db,
                    user_message=user_message,
                    model_config=model_config
                )
                if generated_title:
                    from app.schemas import ConversationUpdate
                    ConversationService.update(
                        db=db,
                        conversation_id=conversation_id,
                        conversation=ConversationUpdate(title=generated_title)
                    )
        except Exception as e:
            if user_message_id:
                try:
                    db.query(Message).filter(Message.id == user_message_id).delete()
                    db.commit()
                except Exception as rollback_error:
                    print(f"回滚用户消息失败: {rollback_error}")
            raise e
