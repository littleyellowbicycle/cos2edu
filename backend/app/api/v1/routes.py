from typing import List, Optional
from datetime import datetime
import os
import uuid
import aiofiles
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel
from starlette.responses import FileResponse

from app.core.limiter import limiter
from app.core.config import settings
from app.core.logging_config import get_logger
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

logger = get_logger(__name__)


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
    character_name: Optional[str] = None
    character_avatar: Optional[str] = None
    character_avatar_type: Optional[str] = None

    class Config:
        from_attributes = True


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


@router.post("/characters/multipart", response_model=CharacterResponse)
@limiter.limit("20/minute")
async def create_character_multipart(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    personality: str = Form(""),
    background: str = Form(""),
    avatar_type: str = Form("emoji"),
    avatar: Optional[UploadFile] = File(None)
):
    avatar_path = None
    
    if avatar and avatar_type == "image":
        file_ext = os.path.splitext(avatar.filename)[1] if avatar.filename else ".png"
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        avatar_path = os.path.join(settings.AVATARS_DIR, unique_filename)
        
        os.makedirs(settings.AVATARS_DIR, exist_ok=True)
        async with aiofiles.open(avatar_path, 'wb') as f:
            content = await avatar.read()
            await f.write(content)
        avatar_path = unique_filename
    
    character_data = CharacterCreate(
        name=name,
        description=description,
        personality=personality,
        background=background,
        avatar=avatar_path,
        avatar_type=avatar_type
    )
    return await CharacterService.create(character_data)


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


@router.put("/characters/{character_id}/multipart", response_model=CharacterResponse)
@limiter.limit("20/minute")
async def update_character_multipart(
    request: Request,
    character_id: int,
    name: str = Form(...),
    description: str = Form(""),
    personality: str = Form(""),
    background: str = Form(""),
    avatar_type: str = Form("emoji"),
    avatar: Optional[UploadFile] = File(None)
):
    avatar_path = None
    
    if avatar and avatar_type == "image":
        file_ext = os.path.splitext(avatar.filename)[1] if avatar.filename else ".png"
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        avatar_path = os.path.join(settings.AVATARS_DIR, unique_filename)
        
        os.makedirs(settings.AVATARS_DIR, exist_ok=True)
        async with aiofiles.open(avatar_path, 'wb') as f:
            content = await avatar.read()
            await f.write(content)
        avatar_path = unique_filename
    
    update_data = {
        "name": name,
        "description": description,
        "personality": personality,
        "background": background,
        "avatar_type": avatar_type
    }
    if avatar_path:
        update_data["avatar"] = avatar_path
    
    character_update = CharacterUpdate(**update_data)
    updated = await CharacterService.update(character_id, character_update)
    if not updated:
        raise HTTPException(status_code=404, detail="角色不存在")
    return updated


@router.delete("/characters/{character_id}")
@limiter.limit("20/minute")
async def delete_character(request: Request, character_id: int):
    if not await CharacterService.delete(character_id):
        raise HTTPException(status_code=404, detail="角色不存在")
    return {"message": "删除成功"}


@router.get("/crud/avatars/{filename}")
async def get_avatar(filename: str):
    avatar_path = os.path.join(settings.AVATARS_DIR, filename)
    if not os.path.exists(avatar_path):
        raise HTTPException(status_code=404, detail="头像不存在")
    return FileResponse(avatar_path)


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


class UploadMaterialResponse(BaseModel):
    content_url: str
    filename: str


@router.post("/materials/upload", response_model=UploadMaterialResponse)
@limiter.limit("10/minute")
async def upload_material(request: Request, file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择文件")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    allowed_exts = ['.txt', '.md', '.markdown', '.text']
    
    if file_ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式，仅支持: {', '.join(allowed_exts)}")
    
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(settings.MATERIALS_DIR, unique_filename)
    os.makedirs(settings.MATERIALS_DIR, exist_ok=True)
    
    content = await file.read()
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text = content.decode('gbk')
        except:
            text = content.decode('utf-8', errors='ignore')
    
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
        await f.write(text)
    
    return UploadMaterialResponse(
        content_url=unique_filename,
        filename=file.filename
    )


@router.post("/materials/{material_id}/generate-summary")
async def generate_material_summary_async(material_id: int):
    from app.services.crud_services import MaterialService
    import asyncio
    
    material = await MaterialService.get_by_id(material_id)
    if not material:
        raise HTTPException(status_code=404, detail="教材不存在")
    
    file_path = os.path.join(settings.MATERIALS_DIR, material.content_url)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="文件不存在")
    
    async def _generate():
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            summary = await _call_llm_for_summary(content)
            
            await MaterialService.update(material_id, {
                "description": summary
            })
            logger.info(f"教材 {material_id} 概括生成成功: {summary[:50]}...")
        except Exception as e:
            logger.error(f"教材 {material_id} 概括生成失败: {e}")
    
    asyncio.create_task(_generate())
    return {"message": "概括生成中..."}


async def _call_llm_for_summary(content: str) -> str:
    from app.services.chat_service import LLMProvider
    from app.services.crud_services import ModelConfigService
    
    try:
        model_config = await ModelConfigService.get_default()
        if not model_config:
            return "请先配置模型"
        
        llm = LLMProvider({
            "provider": model_config.provider,
            "model_name": model_config.model_name,
            "api_key": model_config.api_key,
            "base_url": model_config.base_url,
            "group_id": getattr(model_config, 'group_id', None)
        })
        
        prompt = f"请为以下教材内容生成一个简短概括（不超过100字），概括主要内容和学习要点：\n\n{content[:3000]}"
        
        summary = await llm.chat([
            {"role": "user", "content": prompt}
        ])
        
        return summary.strip()
    except Exception as e:
        logger.error(f"生成教材概括失败: {e}")
        return "概括生成失败"


@router.get("/conversations", response_model=List[CreateConversationResponse])
@limiter.limit("60/minute")
async def get_conversations(request: Request):
    conversations = await ConversationService.get_all()
    result = []
    for conv in conversations:
        char_name = None
        char_avatar = None
        char_avatar_type = None
        if conv.character_id:
            char = await CharacterService.get_by_id(conv.character_id)
            if char:
                char_name = char.name
                char_avatar = char.avatar
                char_avatar_type = char.avatar_type
        result.append({
            "id": conv.id,
            "title": conv.title,
            "character_id": conv.character_id,
            "material_id": conv.material_id,
            "teaching_mode": conv.teaching_mode,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "character_name": char_name,
            "character_avatar": char_avatar,
            "character_avatar_type": char_avatar_type
        })
    return result


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