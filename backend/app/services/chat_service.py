from typing import AsyncIterator, Optional, List, Dict, Any
import json
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.core.config import settings
from app.core.logging_config import get_logger
from app.repositories.unit_of_work import UnitOfWork

logger = get_logger(__name__)


PROVIDER_DEFAULTS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4.1"
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com",
        "model": "claude-sonnet-4-20250514"
    },
    "dashscope": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen3-max"
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4.5"
    },
    "doubao": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "doubao-seed-1.6"
    },
    "wenxin": {
        "base_url": "https://qianfan.baidubce.com/v2",
        "model": "ernie-4.5-8k-preview"
    },
    "hunyuan": {
        "base_url": "https://api.hunyuan.cloud.tencent.com",
        "model": "hunyuan-turbos-latest"
    },
    "moonshot": {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k"
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-2.5-pro"
    },
    "minimax": {
        "base_url": "https://api.minimax.chat/v1",
        "model": "MiniMax-M2.7"
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat"
    },
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "deepseek-ai/DeepSeek-V3"
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "openai/gpt-4.1"
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen3"
    }
}


class LLMProvider:
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        self.model_config = model_config or {}
        self.provider = self.model_config.get("provider", settings.DEFAULT_PROVIDER)
        self.model_name = self.model_config.get("model_name") or PROVIDER_DEFAULTS.get(self.provider, {}).get("model") or settings.DEFAULT_MODEL
        self.api_key = self.model_config.get("api_key") or settings.OPENAI_API_KEY
        self.base_url = self.model_config.get("base_url") or PROVIDER_DEFAULTS.get(self.provider, {}).get("base_url") or settings.OPENAI_BASE_URL
        self.group_id = self.model_config.get("group_id") or getattr(settings, 'MINIMAX_GROUP_ID', None)
        logger.info(f"[LLMProvider] init: provider={self.provider}, model={self.model_name}, base_url={self.base_url}")

    def _validate_config(self):
        if not self.api_key or self.api_key in ("your-openai-api-key", ""):
            raise ValueError(f"请先配置 {self.provider} 的 API Key。访问 /settings 页面进行设置。")
        if not self.model_name:
            raise ValueError("请先选择 AI 模型。访问 /settings 页面进行设置。")

    def _get_client(self):
        extra_headers = {}
        
        if self.provider == "openai":
            return AsyncOpenAI(api_key=self.api_key, base_url=self.base_url or "https://api.openai.com/v1")
        elif self.provider == "anthropic":
            return AsyncAnthropic(api_key=self.api_key, base_url=self.base_url or "https://api.anthropic.com")
        elif self.provider == "minimax":
            return AsyncOpenAI(
                api_key=self.api_key, 
                base_url=self.base_url or "https://api.minimax.chat/v1"
            )
        else:
            return AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        self._validate_config()
        client = self._get_client()
        
        try:
            if self.provider == "anthropic":
                ant_messages = [{"role": m["role"] if m["role"] != "system" else "user", "content": m["content"]} for m in messages]
                system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
                response = await client.messages.create(
                    model=self.model_name,
                    max_tokens=1024,
                    system=system_msg,
                    messages=ant_messages
                )
                return response.content[0].text
            else:
                response = await client.chat.completions.create(
                    model=self.model_name,
                    messages=messages
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM chat error [{self.provider}]: {str(e)}")
            raise

    async def chat_stream(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        self._validate_config()
        client = self._get_client()
        
        try:
            if self.provider == "anthropic":
                ant_messages = [{"role": m["role"] if m["role"] != "system" else "user", "content": m["content"]} for m in messages]
                system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
                stream = await client.messages.create(
                    model=self.model_name,
                    max_tokens=1024,
                    system=system_msg,
                    messages=ant_messages,
                    stream=True
                )
                async for chunk in stream:
                    if chunk.type == "content_block_delta" and hasattr(chunk, 'delta'):
                        yield chunk.delta.text
            else:
                stream = await client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    stream=True
                )
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"LLM stream error [{self.provider}]: {str(e)}")
            raise


class ChatService:
    @staticmethod
    async def chat(
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
                    "base_url": model_config.base_url,
                    "group_id": getattr(model_config, 'group_id', None)
                }
                logger.info(f"[Chat] model_config: provider={model_config.provider}, model={model_config.model_name}, base_url={model_config.base_url}")
            else:
                logger.warning("[Chat] No model_config provided")

            llm = LLMProvider(config_dict)
            response = await llm.chat(messages)
            response = ChatService._strip_think_tags(response)

            await uow.messages.create({
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": response
            })

            return response

    @staticmethod
    async def chat_stream(
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
                    "base_url": model_config.base_url,
                    "group_id": getattr(model_config, 'group_id', None)
                }
                logger.info(f"[Chat] model_config: provider={model_config.provider}, model={model_config.model_name}, base_url={model_config.base_url}")
            else:
                logger.warning("[Chat] No model_config provided")

            llm = LLMProvider(config_dict)

            full_response = ""
            buffer = ""
            
            async for chunk in llm.chat_stream(messages):
                buffer += chunk
                
                while buffer:
                    think_start = buffer.lower().find('<think>')
                    think_end = buffer.lower().find('</think>')
                    
                    if think_start != -1 and think_end != -1:
                        buffer = buffer[:think_start] + buffer[think_end + 6:]
                    elif think_start != -1:
                        to_send = buffer[:think_start]
                        buffer = buffer[think_start + 9:]
                        if to_send:
                            full_response += to_send
                            yield to_send
                        break
                    elif think_end != -1:
                        buffer = buffer[think_end + 6:]
                    else:
                        full_response += buffer
                        yield buffer
                        buffer = ""
                        break
            
            if buffer:
                buffer = buffer.strip()
                if buffer:
                    full_response += buffer
                    yield buffer

            await uow.messages.create({
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": full_response
            })

    @staticmethod
    def _strip_think_tags(content: str) -> str:
        import re
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL | re.IGNORECASE)
        return content.strip()
    
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
            material_content = ""
            if conversation.material.content_type == 'url' and conversation.material.content_url:
                material_content = f"教材URL: {conversation.material.content_url}\n\n请根据这个URL的内容回答用户的问题。"
            elif conversation.material.content:
                material_content = conversation.material.content
            elif conversation.material.content_url:
                import os
                import aiofiles
                file_path = os.path.join(settings.MATERIALS_DIR, conversation.material.content_url)
                if os.path.exists(file_path):
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        material_content = await f.read()
                    if not material_content:
                        raise ValueError(
                            f"教材「{conversation.material.title}」的内容为空，PDF 可能无法提取文字（如扫描版），"
                            f"请转换为文本格式后重新上传"
                        )
                else:
                    raise ValueError(
                        f"教材「{conversation.material.title}」的文件未找到（{conversation.material.content_url}），"
                        f"请重新上传教材文件"
                    )
            
            if not material_content:
                raise ValueError(f"教材「{conversation.material.title}」没有内容。请检查教材是否已上传文件，或内容是否为空。")
            
            messages.append({
                "role": "system",
                "content": f"教材信息: {conversation.material.title}\n\n{material_content}"
            })

        async with UnitOfWork() as uow:
            history = await uow.messages.get_by_conversation(conversation.id)
            for msg in history[-20:]:
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": user_message})
        return messages
