from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
from contextlib import contextmanager

from app.core.database import SessionLocal
from app.core.limiter import limiter
from app.schemas import ChatMessage
from app.services import ChatService, ModelConfigService


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/chat/{conversation_id}")
@limiter.limit("20/minute")
async def chat(
    request: Request,
    conversation_id: int,
    message: ChatMessage,
    model_config_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    model_config = None
    if model_config_id:
        model_config = ModelConfigService.get_by_id(db, model_config_id)
    
    try:
        response = await ChatService.chat(
            db=db,
            conversation_id=conversation_id,
            user_message=message.content,
            model_config=model_config
        )
        return {"response": response}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/chat/{conversation_id}/stream")
@limiter.limit("20/minute")
async def chat_stream(
    request: Request,
    conversation_id: int,
    message: ChatMessage,
    model_config_id: Optional[int] = None,
):
    message_content = message.content
    
    async def generate():
        with get_db_context() as db:
            model_config = None
            if model_config_id:
                model_config = ModelConfigService.get_by_id(db, model_config_id)
            
            try:
                async for chunk in ChatService.chat_stream(
                    db=db,
                    conversation_id=conversation_id,
                    user_message=message_content,
                    model_config=model_config
                ):
                    yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except ValueError as e:
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
