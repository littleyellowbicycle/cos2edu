import asyncio
from typing import List, Optional
from datetime import datetime
import os
import uuid
import io
import aiofiles
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel, ConfigDict
from starlette.responses import FileResponse

from app.core.limiter import limiter
from app.core.config import settings
from app.core.logging_config import get_logger
from app.services.character_card import export_character_card, import_character_card
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
    api_key: str = ""
    base_url: Optional[str] = None
    config_id: Optional[int] = None


class ModelOption(BaseModel):
    value: str
    label: str


class ProviderInfo(BaseModel):
    key: str
    name: str
    base_url: str
    models: List[ModelOption]


class CreateConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
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
    try:
        return await CharacterService.create(character)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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


@router.get("/characters/{character_id}/export-card")
@limiter.limit("10/minute")
async def export_character_card_endpoint(request: Request, character_id: int):
    try:
        png_bytes = await export_character_card(character_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"导出角色卡失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出角色卡失败: {str(e)}")

    character = await CharacterService.get_by_id(character_id)
    filename = f"{character.name}_character_card.png" if character else "character_card.png"

    from starlette.responses import Response
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/characters/import-card")
@limiter.limit("10/minute")
async def import_character_card_endpoint(
    request: Request,
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith(".png"):
        raise HTTPException(status_code=400, detail="仅支持 PNG 格式的角色卡文件")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")

    try:
        result = await import_character_card(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"导入角色卡失败: {e}")
        raise HTTPException(status_code=500, detail=f"导入角色卡失败: {str(e)}")

    return result


@router.get("/avatars/{filename}")
async def get_avatar(filename: str):
    avatar_path = os.path.realpath(os.path.join(settings.AVATARS_DIR, filename))
    if not avatar_path.startswith(os.path.realpath(settings.AVATARS_DIR)):
        raise HTTPException(status_code=403, detail="Forbidden")
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
    created = await MaterialService.create(material)
    if created.id and created.content:
        from app.tasks.material_pipeline import process_material
        from app.repositories.unit_of_work import UnitOfWork
        asyncio.create_task(process_material(
            material_id=created.id,
            file_path="",
            uow_factory=UnitOfWork,
            text=created.content,
        ))
    return created


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
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="请选择文件")

        file_ext = os.path.splitext(file.filename)[1].lower()
        allowed_exts = ['.txt', '.md', '.markdown', '.text', '.pdf']

        if file_ext not in allowed_exts:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式，仅支持: {', '.join(allowed_exts)}")

        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(settings.MATERIALS_DIR, unique_filename)
        os.makedirs(settings.MATERIALS_DIR, exist_ok=True)

        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)

        if file_ext == '.pdf':
            try:
                import pdfplumber
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="PDF解析库未安装，请联系管理员安装 pdfplumber"
                )
            text_parts = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            text = '\n'.join(text_parts)
            if not text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="PDF文件无法提取文字内容，可能是扫描版或图片型PDF，请尝试转换为文本格式后上传"
                )
        else:
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text = content.decode('gbk')
                except:
                    text = content.decode('utf-8', errors='ignore')

        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(text)

        logger.info(f"Uploaded material: filename={file.filename}, size={file_size_mb:.1f}MB, saved_as={unique_filename}")

        return UploadMaterialResponse(
            content_url=unique_filename,
            filename=file.filename
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload material failed: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


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
            
            await MaterialService.update(material_id, MaterialUpdate(description=summary))
            logger.info(f"教材 {material_id} 概括生成成功: {summary[:50]}...")
        except Exception as e:
            logger.error(f"教材 {material_id} 概括生成失败: {e}")
    
    asyncio.create_task(_generate())
    return {"message": "概括生成中..."}


@router.post("/materials/repair-stuck")
async def repair_stuck_materials():
    """Re-process materials stuck at 'parsing' status."""
    from app.tasks.material_pipeline import process_material
    from app.repositories.unit_of_work import UnitOfWork

    async with UnitOfWork() as uow:
        stuck = await uow.materials.get_by_status("parsing")

    if not stuck:
        return {"message": "没有卡住的教学材料", "repaired": 0}

    repaired = []
    for material in stuck:
        if material.content:
            asyncio.create_task(process_material(
                material_id=material.id,
                file_path="",
                uow_factory=UnitOfWork,
                text=material.content,
            ))
            repaired.append(material.id)

    return {"message": f"已触发 {len(repaired)} 个材料的后台处理", "repaired": repaired}


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
    try:
        return await ConversationService.create(conversation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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


PROVIDER_CONFIGS = {
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": [
            {"value": "gpt-4.1", "label": "GPT-4.1 (推荐)"},
            {"value": "gpt-4.1-mini", "label": "GPT-4.1 Mini"},
            {"value": "gpt-4o", "label": "GPT-4o"},
            {"value": "gpt-4o-mini", "label": "GPT-4o Mini"},
            {"value": "gpt-4-turbo", "label": "GPT-4 Turbo"},
        ]
    },
    "anthropic": {
        "name": "Anthropic",
        "base_url": "https://api.anthropic.com",
        "models": [
            {"value": "claude-sonnet-4-20250514", "label": "Claude Sonnet 4 (推荐)"},
            {"value": "claude-opus-4-20250514", "label": "Claude Opus 4"},
            {"value": "claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet"},
            {"value": "claude-3-5-haiku-20241022", "label": "Claude 3.5 Haiku"},
            {"value": "claude-3-opus-20240229", "label": "Claude 3 Opus"},
        ]
    },
    "dashscope": {
        "name": "阿里云 DashScope",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": [
            {"value": "qwen3-max", "label": "Qwen3 Max (推荐)"},
            {"value": "qwen3-plus", "label": "Qwen3 Plus"},
            {"value": "qwen-plus", "label": "Qwen Plus"},
            {"value": "qwen-max", "label": "Qwen Max"},
            {"value": "qwen-turbo", "label": "Qwen Turbo"},
        ]
    },
    "zhipu": {
        "name": "智谱 GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": [
            {"value": "glm-4.5", "label": "GLM-4.5 (推荐)"},
            {"value": "glm-4-plus", "label": "GLM-4 Plus"},
            {"value": "glm-4-flash", "label": "GLM-4 Flash"},
        ]
    },
    "doubao": {
        "name": "豆包 (字节)",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "models": [
            {"value": "doubao-seed-1.6", "label": "豆包 Seed 1.6 (推荐)"},
            {"value": "doubao-pro-32k", "label": "豆包 Pro 32K"},
            {"value": "doubao-lite-32k", "label": "豆包 Lite 32K"},
        ]
    },
    "wenxin": {
        "name": "百度文心",
        "base_url": "https://qianfan.baidubce.com/v2",
        "models": [
            {"value": "ernie-4.5-8k-preview", "label": "ERNIE 4.5 8K (推荐)"},
            {"value": "ernie-4.0-8k-latest", "label": "ERNIE 4.0 8K"},
            {"value": "ernie-3.5-8k", "label": "ERNIE 3.5 8K"},
        ]
    },
    "hunyuan": {
        "name": "腾讯混元",
        "base_url": "https://api.hunyuan.cloud.tencent.com",
        "models": [
            {"value": "hunyuan-turbos-latest", "label": "混元 TurboS (推荐)"},
            {"value": "hunyuan-turbo-latest", "label": "混元 Turbo"},
            {"value": "hunyuan-pro", "label": "混元 Pro"},
        ]
    },
    "moonshot": {
        "name": "月之暗面 (Kimi)",
        "base_url": "https://api.moonshot.cn/v1",
        "models": [
            {"value": "moonshot-v1-8k", "label": "Kimi v1 8K (推荐)"},
            {"value": "moonshot-v1-32k", "label": "Kimi v1 32K"},
            {"value": "moonshot-v1-128k", "label": "Kimi v1 128K"},
        ]
    },
    "gemini": {
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": [
            {"value": "gemini-2.5-pro", "label": "Gemini 2.5 Pro (推荐)"},
            {"value": "gemini-2.5-flash", "label": "Gemini 2.5 Flash"},
            {"value": "gemini-2.0-flash", "label": "Gemini 2.0 Flash"},
        ]
    },
    "minimax": {
        "name": "MiniMax",
        "base_url": "https://api.minimax.chat/v1",
        "models": [
            {"value": "MiniMax-M2.7", "label": "MiniMax M2.7 (推荐)"},
            {"value": "MiniMax-M2.5", "label": "MiniMax M2.5"},
            {"value": "MiniMax-M2.1", "label": "MiniMax M2.1"},
        ]
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "models": [
            {"value": "deepseek-chat", "label": "DeepSeek-V3 (推荐)"},
            {"value": "deepseek-reasoner", "label": "DeepSeek-R1"},
        ]
    },
    "siliconflow": {
        "name": "硅基流动",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": [
            {"value": "deepseek-ai/DeepSeek-V3", "label": "DeepSeek-V3 (推荐)"},
            {"value": "deepseek-ai/DeepSeek-R1", "label": "DeepSeek-R1"},
            {"value": "Qwen/Qwen3-235B-A22B", "label": "Qwen3 235B"},
            {"value": "Qwen/QwQ-32B", "label": "QwQ 32B"},
            {"value": "Pro/zai-org/GLM-4.5", "label": "GLM-4.5"},
        ]
    },
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            {"value": "openai/gpt-4.1", "label": "GPT-4.1 (推荐)"},
            {"value": "anthropic/claude-sonnet-4", "label": "Claude Sonnet 4"},
            {"value": "google/gemini-2.5-pro", "label": "Gemini 2.5 Pro"},
            {"value": "deepseek/deepseek-chat", "label": "DeepSeek-V3"},
        ]
    },
    "ollama": {
        "name": "Ollama (本地)",
        "base_url": "http://localhost:11434/v1",
        "models": [
            {"value": "qwen3", "label": "Qwen3"},
            {"value": "llama3", "label": "Llama 3"},
            {"value": "deepseek-r1", "label": "DeepSeek-R1"},
            {"value": "gemma3", "label": "Gemma 3"},
            {"value": "mistral", "label": "Mistral"},
        ]
    },
}


@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers():
    return [
        ProviderInfo(key=k, name=v["name"], base_url=v["base_url"], models=v["models"])
        for k, v in PROVIDER_CONFIGS.items()
    ]


class ModelFetchRequest(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None


async def _fetch_models_from_api(provider: str, api_key: str, base_url: str) -> Optional[List[dict]]:
    import httpx
    
    if not api_key:
        return None
    
    provider_config = PROVIDER_CONFIGS.get(provider)
    if not base_url:
        base_url = provider_config["base_url"] if provider_config else ""
    if not base_url:
        return None
    
    base_url = base_url.rstrip("/")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if provider == "gemini":
                url = f"{base_url}/v1beta/models"
                resp = await client.get(url, params={"key": api_key})
                if resp.status_code == 200:
                    data = resp.json()
                    models = data.get("models", [])
                    if models:
                        return [
                            {"value": m["name"].replace("models/", ""), "label": m.get("displayName", m["name"].replace("models/", ""))}
                            for m in models
                            if "gemini" in m.get("name", "").lower()
                        ]
            
            elif provider == "anthropic":
                url = f"{base_url}/v1/models"
                resp = await client.get(url, headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                })
                if resp.status_code == 200:
                    data = resp.json()
                    models = data.get("data", [])
                    if models:
                        return [{"value": m["id"], "label": m.get("display_name", m["id"])} for m in models]
            
            else:
                url = f"{base_url}/models"
                resp = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
                if resp.status_code != 200:
                    url = f"{base_url}/v1/models"
                    resp = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
                
                if resp.status_code == 200:
                    data = resp.json()
                    models = data.get("data", [])
                    if models:
                        return [{"value": m["id"], "label": m["id"]} for m in models]
    except Exception:
        pass
    
    return None


@router.get("/providers/{provider}/models", response_model=List[ModelOption])
async def get_provider_models(
    provider: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
):
    config = PROVIDER_CONFIGS.get(provider)
    if not config:
        raise HTTPException(status_code=404, detail=f"不支持的提供商: {provider}")
    
    if api_key:
        fetched = await _fetch_models_from_api(provider, api_key, base_url)
        if fetched:
            return [ModelOption(**m) for m in fetched]
    
    return [ModelOption(**m) for m in config["models"]]


@router.get("/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    return {"status": "ok", "message": "苏格拉底AI教学系统运行中"}


@router.post("/ai/test")
@limiter.limit("10/minute")
async def test_ai_connection(request: Request, config: TestConfigRequest):
    from app.services.chat_service import LLMProvider
    from app.services.crud_services import ModelConfigService

    try:
        api_key = config.api_key
        if not api_key and config.config_id:
            saved = await ModelConfigService.get_by_id(config.config_id)
            if saved and saved.api_key:
                api_key = saved.api_key

        provider = LLMProvider({
            "provider": config.provider,
            "model_name": config.model,
            "api_key": api_key,
            "base_url": config.base_url
        })

        test_messages = [{"role": "user", "content": "Hi"}]
        response = await provider.chat(test_messages)

        return {"success": True, "response": response[:100]}
    except Exception as e:
        return {"success": False, "error": str(e)}