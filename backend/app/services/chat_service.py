from typing import AsyncIterator, Optional, List, Dict, Any
import json
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.core.config import settings
from app.core.logging_config import get_logger
from models.conversation import Conversation
from models.message import Message
from app.repositories.unit_of_work import UnitOfWork

logger = get_logger(__name__)


class LLMProvider:
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        self.model_config = model_config or {}
        self.provider = self.model_config.get("provider", settings.DEFAULT_PROVIDER)
        self.model_name = self.model_config.get("model_name", settings.DEFAULT_MODEL)
        self.api_key = self.model_config.get("api_key") or settings.OPENAI_API_KEY
        self.base_url = self.model_config.get("base_url") or settings.OPENAI_BASE_URL

    def _get_client(self):
        if self.provider == "openai":
            return AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        elif self.provider == "anthropic":
            return AsyncAnthropic(api_key=self.api_key)
        else:
            return AsyncOpenAI(api_key=self.api_key)

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        if self.provider == "openai":
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        elif self.provider == "anthropic":
            response = await client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                messages=messages
            )
            return response.content[0].text
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def chat_stream(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        client = self._get_client()
        if self.provider == "openai":
            stream = await client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        elif self.provider == "anthropic":
            stream = await client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                messages=messages,
                stream=True
            )
            async for chunk in stream:
                if chunk.type == "content_block_delta" and hasattr(chunk, 'delta'):
                    yield chunk.delta.text
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")


class ChatService:
    @staticmethod
    async def chat(
        db: AsyncSession,
        conversation_id: int,
        user_message: str,
        model_config: Optional[Any] = None
    ) -> str:
        async with UnitOfWork() as uow:
            conversation = await uow.conversations.get_by_id(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")

            await uow.messages.create({
                "conversation_id": conversation_id,
                "role": "user",
                "content": user_message
            })

            messages = await ChatService._build_messages(conversation, user_message)

            config_dict = None
            if model_config:
                config_dict = {
                    "provider": model_config.provider,
                    "model_name": model_config.model_name,
                    "api_key": model_config.api_key,
                    "base_url": model_config.base_url
                }

            llm = LLMProvider(config_dict)
            response = await llm.chat(messages)

            await uow.messages.create({
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": response
            })

            return response

    @staticmethod
    async def chat_stream(
        db: AsyncSession,
        conversation_id: int,
        user_message: str,
        model_config: Optional[Any] = None
    ) -> AsyncIterator[str]:
        async with UnitOfWork() as uow:
            conversation = await uow.conversations.get_by_id(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")

            await uow.messages.create({
                "conversation_id": conversation_id,
                "role": "user",
                "content": user_message
            })

            messages = await ChatService._build_messages(conversation, user_message)

            config_dict = None
            if model_config:
                config_dict = {
                    "provider": model_config.provider,
                    "model_name": model_config.model_name,
                    "api_key": model_config.api_key,
                    "base_url": model_config.base_url
                }

            llm = LLMProvider(config_dict)

            full_response = ""
            async for chunk in llm.chat_stream(messages):
                full_response += chunk
                yield chunk

            await uow.messages.create({
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": full_response
            })

    @staticmethod
    async def _build_messages(conversation, user_message: str) -> List[Dict[str, str]]:
        messages = []

        if conversation.character:
            system_prompt = f"你扮演的角色是 {conversation.character.name}。"
            if conversation.character.personality:
                system_prompt += f" 性格特点: {conversation.character.personality}"
            if conversation.character.background:
                system_prompt += f" 背景: {conversation.character.background}"
            messages.append({"role": "system", "content": system_prompt})

        if conversation.material:
            messages.append({
                "role": "system",
                "content": f"教材信息: {conversation.material.title} - {conversation.material.content}"
            })

        async with UnitOfWork() as uow:
            history = await uow.messages.get_by_conversation(conversation.id)
            for msg in history[-20:]:
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": user_message})
        return messages