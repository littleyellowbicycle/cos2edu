from abc import ABC, abstractmethod
from typing import List, Dict, Optional, AsyncIterator
from app.core.config import settings


class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncIterator[str]:
        pass


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_url or settings.OPENAI_BASE_URL
        
    async def _get_client(self):
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        client = await self._get_client()
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return response.choices[0].message.content

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncIterator[str]:
        client = await self._get_client()
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and hasattr(delta, 'content') and delta.content:
                    yield delta.content


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY

    async def _get_client(self):
        from anthropic import AsyncAnthropic
        return AsyncAnthropic(api_key=self.api_key)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        client = await self._get_client()
        
        system_prompt = ""
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                filtered_messages.append(msg)
        
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt if system_prompt else None,
            messages=filtered_messages,
            **kwargs
        )
        return response.content[0].text

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncIterator[str]:
        client = await self._get_client()
        
        system_prompt = ""
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                filtered_messages.append(msg)
        
        async with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt if system_prompt else None,
            messages=filtered_messages,
            **kwargs
        ) as stream:
            async for text in stream.text_stream:
                yield text


class DashScopeProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.DASHSCOPE_API_KEY
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    async def _get_client(self):
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "qwen-plus",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        client = await self._get_client()
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return response.choices[0].message.content

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "qwen-plus",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncIterator[str]:
        client = await self._get_client()
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and hasattr(delta, 'content') and delta.content:
                    yield delta.content


class ZhipuProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ZHIPU_API_KEY
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/"

    async def _get_client(self):
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "glm-4",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        client = await self._get_client()
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return response.choices[0].message.content

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "glm-4",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncIterator[str]:
        client = await self._get_client()
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and hasattr(delta, 'content') and delta.content:
                    yield delta.content


PROVIDER_MAP = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "dashscope": DashScopeProvider,
    "zhipu": ZhipuProvider,
}


class DoubaoProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.DOUBAO_API_KEY
        self.base_url = base_url or settings.DOUBAO_BASE_URL or "https://ark.cn-beijing.volces.com/api/v3"
    
    async def _get_client(self):
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "doubao-pro-32k",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        client = await self._get_client()
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return response.choices[0].message.content

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "doubao-pro-32k",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncIterator[str]:
        client = await self._get_client()
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and hasattr(delta, 'content') and delta.content:
                    yield delta.content


class WenxinProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.WENXIN_API_KEY
        self.base_url = base_url or settings.WENXIN_BASE_URL or "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop"
    
    async def _get_access_token(self) -> str:
        if not self.api_key:
            raise ValueError("未配置文心一言API Key")
        
        import aiohttp
        api_key, secret_key = self._parse_api_key(self.api_key)
        
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as response:
                data = await response.json()
                if "access_token" in data:
                    return data["access_token"]
                else:
                    raise ValueError(f"获取文心一言access_token失败: {data}")
    
    def _parse_api_key(self, api_key: str) -> tuple:
        if "|" in api_key:
            parts = api_key.split("|")
            return parts[0].strip(), parts[1].strip()
        return api_key, ""

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "ERNIE-4.0-8K",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        access_token = await self._get_access_token()
        
        import aiohttp
        url = f"{self.base_url}/chat/{model}?access_token={access_token}"
        
        system_prompt = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                chat_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "messages": chat_messages,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system_prompt:
            payload["system"] = system_prompt
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                data = await response.json()
                if "result" in data:
                    return data["result"]
                else:
                    raise ValueError(f"文心一言API调用失败: {data}")

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "ERNIE-4.0-8K",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncIterator[str]:
        access_token = await self._get_access_token()
        
        import aiohttp
        url = f"{self.base_url}/chat/{model}?access_token={access_token}"
        
        system_prompt = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                chat_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "messages": chat_messages,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "stream": True
        }
        if system_prompt:
            payload["system"] = system_prompt
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                async for line in response.content:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:].strip()
                        if data:
                            try:
                                import json
                                parsed = json.loads(data)
                                if "result" in parsed and parsed["result"]:
                                    yield parsed["result"]
                            except:
                                pass


class HunyuanProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.HUNYUAN_API_KEY
        self.base_url = base_url or settings.HUNYUAN_BASE_URL or "https://api.hunyuan.cloud.tencent.com/v1"
    
    async def _get_client(self):
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "hunyuan-lite",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        client = await self._get_client()
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return response.choices[0].message.content

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "hunyuan-lite",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncIterator[str]:
        client = await self._get_client()
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and hasattr(delta, 'content') and delta.content:
                    yield delta.content


class MoonshotProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.MOONSHOT_API_KEY
        self.base_url = base_url or settings.MOONSHOT_BASE_URL or "https://api.moonshot.cn/v1"
    
    async def _get_client(self):
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "moonshot-v1-8k",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        client = await self._get_client()
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return response.choices[0].message.content

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "moonshot-v1-8k",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncIterator[str]:
        client = await self._get_client()
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and hasattr(delta, 'content') and delta.content:
                    yield delta.content


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.base_url = base_url or settings.GEMINI_BASE_URL or "https://generativelanguage.googleapis.com/v1beta"
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        import aiohttp
        
        system_prompt = ""
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
        
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                data = await response.json()
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        return candidate["content"]["parts"][0].get("text", "")
                raise ValueError(f"Gemini API调用失败: {data}")

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncIterator[str]:
        import aiohttp
        
        system_prompt = ""
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
        
        url = f"{self.base_url}/models/{model}:streamGenerateContent?key={self.api_key}&alt=sse"
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                async for line in response.content:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:].strip()
                        if data:
                            try:
                                import json
                                parsed = json.loads(data)
                                if "candidates" in parsed and len(parsed["candidates"]) > 0:
                                    candidate = parsed["candidates"][0]
                                    if "content" in candidate and "parts" in candidate["content"]:
                                        text = candidate["content"]["parts"][0].get("text", "")
                                        if text:
                                            yield text
                            except:
                                pass


PROVIDER_MAP.update({
    "doubao": DoubaoProvider,
    "wenxin": WenxinProvider,
    "hunyuan": HunyuanProvider,
    "moonshot": MoonshotProvider,
    "gemini": GeminiProvider,
})


def get_provider(provider_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None) -> BaseLLMProvider:
    provider_name_lower = provider_name.lower()
    provider_class = PROVIDER_MAP.get(provider_name_lower)
    
    if provider_class:
        if provider_name_lower in ["openai", "dashscope", "zhipu", "doubao", "hunyuan", "moonshot", "gemini"]:
            return provider_class(api_key=api_key, base_url=base_url)
        else:
            return provider_class(api_key=api_key)
    
    if base_url:
        return OpenAIProvider(api_key=api_key, base_url=base_url)
    
    raise ValueError(f"不支持的模型提供商: {provider_name}。如果是自定义OpenAI兼容服务，请提供 Base URL。")
