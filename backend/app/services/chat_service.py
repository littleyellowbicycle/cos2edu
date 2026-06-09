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
                ant_messages = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
                system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
                response = await client.messages.create(
                    model=self.model_name,
                    max_tokens=1024,
                    system=system_msg,
                    messages=ant_messages
                )
                content = response.content[0].text
            else:
                response = await client.chat.completions.create(
                    model=self.model_name,
                    messages=messages
                )
                msg = response.choices[0].message
                content = msg.content
                if not content and hasattr(msg, 'reasoning_content') and msg.reasoning_content:
                    logger.info(f"[LLMProvider] content is None, using reasoning_content as fallback")
                    content = msg.reasoning_content

            if content:
                content = ChatService._strip_think_tags(content)
            return content or ""
        except Exception as e:
            logger.error(f"LLM chat error [{self.provider}]: {str(e)}")
            raise

    async def chat_stream(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> AsyncIterator[dict]:
        self._validate_config()
        client = self._get_client()

        try:
            if self.provider == "anthropic":
                ant_messages = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
                system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)

                anthropic_tools = []
                if tools:
                    for t in tools:
                        func = t.get("function", {})
                        anthropic_tools.append({
                            "name": func.get("name", ""),
                            "description": func.get("description", ""),
                            "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                        })

                create_kwargs = {
                    "model": self.model_name,
                    "max_tokens": 1024,
                    "messages": ant_messages,
                    "stream": True,
                }
                if system_msg:
                    create_kwargs["system"] = system_msg
                if anthropic_tools:
                    create_kwargs["tools"] = anthropic_tools

                stream = await client.messages.create(**create_kwargs)
                anthropic_tool_calls = {}
                async for chunk in stream:
                    if chunk.type == "content_block_delta" and hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                        yield {"type": "text", "content": chunk.delta.text}
                    elif chunk.type == "content_block_start" and hasattr(chunk, 'content_block') and chunk.content_block.type == "tool_use":
                        block_idx = chunk.index if hasattr(chunk, 'index') else len(anthropic_tool_calls)
                        anthropic_tool_calls[block_idx] = {
                            "id": chunk.content_block.id,
                            "name": chunk.content_block.name,
                            "arguments": "",
                        }
                    elif chunk.type == "content_block_delta" and hasattr(chunk, 'delta') and chunk.delta.type == "input_json_delta":
                        block_idx = getattr(chunk, 'index', 0)
                        if block_idx in anthropic_tool_calls:
                            anthropic_tool_calls[block_idx]["arguments"] += chunk.delta.partial_json

                if anthropic_tool_calls:
                    yield {
                        "type": "tool_calls",
                        "tool_calls": list(anthropic_tool_calls.values()),
                    }
            else:
                create_kwargs = {
                    "model": self.model_name,
                    "messages": messages,
                    "stream": True,
                }
                if tools:
                    create_kwargs["tools"] = tools

                stream = await client.chat.completions.create(**create_kwargs)

                tool_calls_accumulator = {}
                async for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta and delta.content:
                        yield {"type": "text", "content": delta.content}

                    if delta and hasattr(delta, 'tool_calls') and delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index if hasattr(tc, 'index') and tc.index is not None else 0
                            if idx not in tool_calls_accumulator:
                                tool_calls_accumulator[idx] = {"id": "", "name": "", "arguments": ""}
                            if hasattr(tc, 'id') and tc.id:
                                tool_calls_accumulator[idx]["id"] = tc.id
                            if hasattr(tc, 'function') and tc.function:
                                if tc.function.name:
                                    tool_calls_accumulator[idx]["name"] = tc.function.name
                                if tc.function.arguments:
                                    tool_calls_accumulator[idx]["arguments"] += tc.function.arguments

                    finish_reason = chunk.choices[0].finish_reason if chunk.choices else None
                    if finish_reason == "tool_calls" and tool_calls_accumulator:
                        yield {
                            "type": "tool_calls",
                            "tool_calls": list(tool_calls_accumulator.values()),
                        }
                        tool_calls_accumulator.clear()

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

        import re

        full_response = ""
        buffer = ""
        in_think = False

        async for event in llm.chat_stream(messages):
            if event["type"] == "text":
                chunk = event["content"]
            else:
                continue

            buffer += chunk

            while buffer:
                if in_think:
                    close_pos = buffer.lower().find('</think>')
                    if close_pos != -1:
                        in_think = False
                        buffer = buffer[close_pos + 8:]
                    else:
                        buffer = ""
                        break
                else:
                    open_pos = buffer.lower().find('<think>')
                    close_pos = buffer.lower().find('</think>')
                    if open_pos != -1 and (close_pos == -1 or open_pos < close_pos):
                        to_send = buffer[:open_pos]
                        buffer = buffer[open_pos + 7:]
                        in_think = True
                        if to_send:
                            full_response += to_send
                            yield to_send
                    elif close_pos != -1:
                        # Orphan </think> without opening — strip it
                        buffer = buffer[:close_pos] + buffer[close_pos + 8:]
                    else:
                        # Hold back any content that could start <think> across chunks
                        hold = 0
                        last_lt = buffer.rfind('<')
                        if last_lt != -1:
                            suffix = buffer[last_lt:].lower()
                            think_prefixes = ['<think>', '<think', '</think>', '</think']
                            for p in think_prefixes:
                                if p.startswith(suffix):
                                    hold = len(buffer) - last_lt
                                    break
                        if hold and hold < len(buffer):
                            safe = buffer[:-hold]
                            buffer = buffer[-hold:]
                            if safe:
                                full_response += safe
                                yield safe
                        elif hold >= len(buffer):
                            # Entire buffer is a potential tag prefix — hold all
                            break
                        else:
                            full_response += buffer
                            yield buffer
                            buffer = ""
                        break

        if buffer:
            buffer = re.sub(r'<think>.*?</think>', '', buffer, flags=re.DOTALL | re.IGNORECASE)
            buffer = buffer.strip()
            if buffer:
                full_response += buffer
                yield buffer

        async with UnitOfWork() as uow:
            await uow.messages.create({
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": full_response
            })

    @staticmethod
    def _strip_think_tags(content: str) -> str:
        import re
        content = re.sub(r'<think\b.*?</think\s*>?', '', content, flags=re.DOTALL | re.IGNORECASE)
        return content.strip()
    
    @staticmethod
    async def _build_messages(conversation, user_message: str) -> List[Dict[str, str]]:
        messages = []
        system_parts = []

        if conversation.character:
            system_prompt = f"你扮演的角色是 {conversation.character.name}。"
            if conversation.character.personality:
                system_prompt += f" 性格特点: {conversation.character.personality}"
            if conversation.character.background:
                system_prompt += f" 背景: {conversation.character.background}"
            system_parts.append(system_prompt)

        if conversation.material and conversation.material.status == "ready":
            material_title = conversation.material.title

            # Try RAG retrieval first
            rag_context = ""
            try:
                from app.services.rag_service import get_rag_service
                rag = get_rag_service()
                if rag.is_ready:
                    rag_context = rag.get_context(user_message, max_tokens=1500)
            except Exception:
                pass

            if rag_context:
                system_parts.append(f"教材信息: {material_title}\n\n参考资料:\n{rag_context}")
            else:
                # Fallback: read raw content
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
                                f"教材「{material_title}」的内容为空，PDF 可能无法提取文字（如扫描版），"
                                f"请转换为文本格式后重新上传"
                            )
                    else:
                        raise ValueError(
                            f"教材「{material_title}」的文件未找到（{conversation.material.content_url}），"
                            f"请重新上传教材文件"
                        )

                if not material_content:
                    raise ValueError(f"教材「{material_title}」没有内容。请检查教材是否已上传文件，或内容是否为空。")

                if len(material_content) > 4000:
                    material_content = material_content[:4000] + "\n\n... (内容过长已截断，请询问用户是否需要了解更详细的教材信息)"

                system_parts.append(f"教材信息: {material_title}\n\n{material_content}")

        if system_parts:
            messages.append({"role": "system", "content": "\n\n".join(system_parts)})

        async with UnitOfWork() as uow:
            history = await uow.messages.get_by_conversation(conversation.id)
            for msg in history[-20:]:
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": user_message})
        return messages
