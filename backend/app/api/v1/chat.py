"""
Chat API Module - 聊天接口模块

提供聊天相关的 API 端点，包括同步聊天和流式聊天功能。
负责处理并发请求限制和客户端身份识别。

核心功能：
- 同步聊天接口 (/chat/{conversation_id})
- 流式聊天接口 (/chat/{conversation_id}/stream)
- 并发请求锁机制
- 客户端身份识别（基于 IP 地址）

模块结构：
- router: FastAPI 路由对象
- get_client_identifier(): 从请求中提取客户端标识符
- acquire_concurrency_lock(): 获取并发锁
- get_model_config(): 获取模型配置
- chat(): 同步聊天端点
- chat_stream(): 流式聊天端点
"""

from typing import Optional, AsyncIterator
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
import json

from app.core.limiter import limiter
from app.core.concurrency import concurrency_lock
from app.schemas import ChatMessage
from app.services import ChatService, ModelConfigService

router = APIRouter()


# ============================================================================
# 辅助函数 / Helper Functions
# ============================================================================


def get_client_identifier(request: Request) -> str:
    """从请求中提取客户端标识符
    
    优先从 X-Forwarded-For 或 X-Real-IP 头部获取，
    最后回退到请求的客户端IP。
    
    Args:
        request: FastAPI 请求对象
        
    Returns:
        客户端标识符字符串
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip
    
    if request.client and request.client.host:
        return request.client.host
    
    return "unknown"


async def acquire_concurrency_lock(client_id: str, conversation_id: int, lock_type: str) -> str:
    """获取并发锁
    
    尝试获取指定类型的并发锁，如果锁已被持有则抛出 HTTP 429 错误。
    
    Args:
        client_id: 客户端标识符
        conversation_id: 对话 ID
        lock_type: 锁类型（如 'chat', 'stream'）
        
    Returns:
        锁的唯一键值
        
    Raises:
        HTTPException: 当锁已被持有时，抛出 429 状态码
    """
    lock_key = f"request:{lock_type}:{client_id}:{conversation_id}"
    lock_acquired = await concurrency_lock.acquire(lock_key)
    
    if not lock_acquired:
        raise HTTPException(
            status_code=429,
            detail={
                "error": f"concurrent_{lock_type}_not_allowed",
                "message": f"当前已有正在进行的{lock_type}请求，请等待完成后再发起新请求"
            }
        )
    
    return lock_key


async def get_model_config(model_config_id: Optional[int]):
    if model_config_id is not None:
        return await ModelConfigService.get_by_id(model_config_id)
    return await ModelConfigService.get_default()


# ============================================================================
# API 端点 / API Endpoints
# ============================================================================


@router.post("/{conversation_id}")
@limiter.limit("20/minute")
async def chat(
    request: Request,
    conversation_id: int,
    message: ChatMessage,
    model_config_id: Optional[int] = None,
):
    """同步聊天接口
    
    处理用户的同步聊天请求，返回完整的 AI 响应。
    
    Args:
        request: FastAPI 请求对象
        conversation_id: 对话 ID
        message: 包含用户消息内容的请求体
        model_config_id: 可选的模型配置 ID
        
    Returns:
        包含响应内容的字典 {"response": str}
        
    Raises:
        HTTPException: 400 - 对话不存在或参数错误
        HTTPException: 429 - 并发请求限制
    """
    client_id = get_client_identifier(request)
    lock_key = await acquire_concurrency_lock(client_id, conversation_id, "chat")
    
    try:
        model_config = await get_model_config(model_config_id)
        
        response = await ChatService.chat(
            conversation_id=conversation_id,
            user_message=message.content,
            model_config=model_config
        )
        return {"response": response}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    finally:
        await concurrency_lock.release(lock_key)


@router.post("/{conversation_id}/stream")
@limiter.limit("20/minute")
async def chat_stream(
    request: Request,
    conversation_id: int,
    message: ChatMessage,
    model_config_id: Optional[int] = None,
):
    """流式聊天接口
    
    处理用户的流式聊天请求，以 Server-Sent Events 方式返回 AI 响应。
    
    Args:
        request: FastAPI 请求对象
        conversation_id: 对话 ID
        message: 包含用户消息内容的请求体
        model_config_id: 可选的模型配置 ID
        
    Returns:
        StreamingResponse: 流式响应对象
        
    Raises:
        HTTPException: 429 - 并发请求限制
    """
    client_id = get_client_identifier(request)
    lock_key = await acquire_concurrency_lock(client_id, conversation_id, "stream")
    
    message_content = message.content
    
    async def generate() -> AsyncIterator[str]:
        try:
            model_config = await get_model_config(model_config_id)
            
            try:
                async for chunk in ChatService.chat_stream(
                    conversation_id=conversation_id,
                    user_message=message_content,
                    model_config=model_config
                ):
                    yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            
            except ValueError as e:
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            
            except Exception as e:
                yield f"data: {json.dumps({'error': f'流式响应错误: {str(e)}'}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
        
        finally:
            await concurrency_lock.release(lock_key)
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )