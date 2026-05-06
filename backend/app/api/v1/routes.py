from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.limiter import limiter
from app.schemas import (
    CharacterCreate, CharacterUpdate, CharacterResponse,
    MaterialCreate, MaterialUpdate, MaterialResponse,
    ConversationCreate, ConversationUpdate, 
    ConversationResponse, ConversationWithMessages,
    MessageResponse,
    ModelConfigCreate, ModelConfigUpdate, ModelConfigResponse,
)
from app.services import (
    CharacterService, MaterialService,
    ConversationService, MessageService, ModelConfigService
)


router = APIRouter()


class TestConfigRequest(BaseModel):
    provider: str
    model: str
    api_key: str
    base_url: Optional[str] = None


class CreateConversationResponse(BaseModel):
    id: int
    title: Optional[str] = None
    character_id: Optional[int] = None
    material_id: Optional[int] = None
    teaching_mode: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


router = APIRouter()


@router.get("/characters", response_model=List[CharacterResponse])
@limiter.limit("60/minute")
async def get_characters(request: Request):
    return await CharacterService.get_all()


@router.get("/characters/{character_id}", response_model=CharacterResponse)
@limiter.limit("60/minute")
async def get_character(request: Request, character_id: int):
    character = await CharacterService.get_by_id(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    return character


@router.post("/characters", response_model=CharacterResponse)
@limiter.limit("20/minute")
async def create_character(request: Request, character: CharacterCreate):
    return await CharacterService.create(character)


@router.put("/characters/{character_id}", response_model=CharacterResponse)
@limiter.limit("20/minute")
async def update_character(
    request: Request,
    character_id: int, 
    character: CharacterUpdate
):
    updated = await CharacterService.update(character_id, character)
    if not updated:
        raise HTTPException(status_code=404, detail="角色不存在")
    return updated


@router.delete("/characters/{character_id}")
@limiter.limit("20/minute")
async def delete_character(request: Request, character_id: int):
    if not await CharacterService.delete(character_id):
        raise HTTPException(status_code=404, detail="角色不存在")
    return {"message": "删除成功"}


@router.get("/materials", response_model=List[MaterialResponse])
@limiter.limit("60/minute")
async def get_materials(request: Request):
    return await MaterialService.get_all()


@router.get("/materials/{material_id}", response_model=MaterialResponse)
@limiter.limit("60/minute")
async def get_material(request: Request, material_id: int):
    material = await MaterialService.get_by_id(material_id)
    if not material:
        raise HTTPException(status_code=404, detail="教材不存在")
    return material


@router.post("/materials", response_model=MaterialResponse)
@limiter.limit("20/minute")
async def create_material(request: Request, material: MaterialCreate):
    return await MaterialService.create(material)


@router.put("/materials/{material_id}", response_model=MaterialResponse)
@limiter.limit("20/minute")
async def update_material(
    request: Request,
    material_id: int, 
    material: MaterialUpdate
):
    updated = await MaterialService.update(material_id, material)
    if not updated:
        raise HTTPException(status_code=404, detail="教材不存在")
    return updated


@router.delete("/materials/{material_id}")
@limiter.limit("20/minute")
async def delete_material(request: Request, material_id: int):
    if not await MaterialService.delete(material_id):
        raise HTTPException(status_code=404, detail="教材不存在")
    return {"message": "删除成功"}


@router.get("/conversations", response_model=List[CreateConversationResponse])
@limiter.limit("60/minute")
async def get_conversations(request: Request):
    return await ConversationService.get_all()


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
@limiter.limit("60/minute")
async def get_conversation(request: Request, conversation_id: int):
    conversation = await ConversationService.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    messages = await MessageService.get_by_conversation(conversation_id)
    
    character = None
    if conversation.character_id:
        character = await CharacterService.get_by_id(conversation.character_id)
    
    material = None
    if conversation.material_id:
        material = await MaterialService.get_by_id(conversation.material_id)
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "character_id": conversation.character_id,
        "material_id": conversation.material_id,
        "teaching_mode": conversation.teaching_mode,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "character": character,
        "material": material,
        "messages": messages
    }


@router.post("/conversations", response_model=CreateConversationResponse)
@limiter.limit("30/minute")
async def create_conversation(request: Request, conversation: ConversationCreate):
    return await ConversationService.create(conversation)


@router.put("/conversations/{conversation_id}", response_model=CreateConversationResponse)
@limiter.limit("30/minute")
async def update_conversation(
    request: Request,
    conversation_id: int, 
    conversation: ConversationUpdate
):
    updated = await ConversationService.update(conversation_id, conversation)
    if not updated:
        raise HTTPException(status_code=404, detail="对话不存在")
    return updated


@router.delete("/conversations/{conversation_id}")
@limiter.limit("30/minute")
async def delete_conversation(request: Request, conversation_id: int):
    if not await ConversationService.delete(conversation_id):
        raise HTTPException(status_code=404, detail="对话不存在")
    return {"message": "删除成功"}


@router.get("/model-configs", response_model=List[ModelConfigResponse])
@limiter.limit("60/minute")
async def get_model_configs(request: Request):
    return await ModelConfigService.get_all()


@router.get("/model-configs/{config_id}", response_model=ModelConfigResponse)
@limiter.limit("60/minute")
async def get_model_config(request: Request, config_id: int):
    config = await ModelConfigService.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return config


@router.post("/model-configs", response_model=ModelConfigResponse)
@limiter.limit("20/minute")
async def create_model_config(request: Request, config: ModelConfigCreate):
    return await ModelConfigService.create(config)


@router.put("/model-configs/{config_id}", response_model=ModelConfigResponse)
@limiter.limit("20/minute")
async def update_model_config(
    request: Request,
    config_id: int, 
    config: ModelConfigUpdate
):
    updated = await ModelConfigService.update(config_id, config)
    if not updated:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return updated


@router.delete("/model-configs/{config_id}")
@limiter.limit("20/minute")
async def delete_model_config(request: Request, config_id: int):
    if not await ModelConfigService.delete(config_id):
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return {"message": "删除成功"}


@router.get("/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    return {"status": "ok", "message": "苏格拉底AI教学系统运行中"}


@router.post("/ai/test")
@limiter.limit("10/minute")
async def test_ai_connection(request: Request, config: TestConfigRequest):
    from app.services.chat_service import LLMProvider
    
    try:
        provider = LLMProvider({
            "provider": config.provider,
            "model_name": config.model,
            "api_key": config.api_key,
            "base_url": config.base_url
        })
        
        test_messages = [{"role": "user", "content": "Hi"}]
        response = await provider.chat(test_messages)
        
        return {"success": True, "response": response[:100]}
    except Exception as e:
        return {"success": False, "error": str(e)}