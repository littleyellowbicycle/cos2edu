from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/characters", response_model=List[CharacterResponse])
@limiter.limit("60/minute")
def get_characters(request: Request, db: Session = Depends(get_db)):
    return CharacterService.get_all(db)


@router.get("/characters/{character_id}", response_model=CharacterResponse)
@limiter.limit("60/minute")
def get_character(request: Request, character_id: int, db: Session = Depends(get_db)):
    character = CharacterService.get_by_id(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    return character


@router.post("/characters", response_model=CharacterResponse)
@limiter.limit("20/minute")
def create_character(request: Request, character: CharacterCreate, db: Session = Depends(get_db)):
    return CharacterService.create(db, character)


@router.put("/characters/{character_id}", response_model=CharacterResponse)
@limiter.limit("20/minute")
def update_character(
    request: Request,
    character_id: int, 
    character: CharacterUpdate, 
    db: Session = Depends(get_db)
):
    updated = CharacterService.update(db, character_id, character)
    if not updated:
        raise HTTPException(status_code=404, detail="角色不存在")
    return updated


@router.delete("/characters/{character_id}")
@limiter.limit("20/minute")
def delete_character(request: Request, character_id: int, db: Session = Depends(get_db)):
    if not CharacterService.delete(db, character_id):
        raise HTTPException(status_code=404, detail="角色不存在")
    return {"message": "删除成功"}


@router.get("/materials", response_model=List[MaterialResponse])
@limiter.limit("60/minute")
def get_materials(request: Request, db: Session = Depends(get_db)):
    return MaterialService.get_all(db)


@router.get("/materials/{material_id}", response_model=MaterialResponse)
@limiter.limit("60/minute")
def get_material(request: Request, material_id: int, db: Session = Depends(get_db)):
    material = MaterialService.get_by_id(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="教材不存在")
    return material


@router.post("/materials", response_model=MaterialResponse)
@limiter.limit("20/minute")
def create_material(request: Request, material: MaterialCreate, db: Session = Depends(get_db)):
    return MaterialService.create(db, material)


@router.put("/materials/{material_id}", response_model=MaterialResponse)
@limiter.limit("20/minute")
def update_material(
    request: Request,
    material_id: int, 
    material: MaterialUpdate, 
    db: Session = Depends(get_db)
):
    updated = MaterialService.update(db, material_id, material)
    if not updated:
        raise HTTPException(status_code=404, detail="教材不存在")
    return updated


@router.delete("/materials/{material_id}")
@limiter.limit("20/minute")
def delete_material(request: Request, material_id: int, db: Session = Depends(get_db)):
    if not MaterialService.delete(db, material_id):
        raise HTTPException(status_code=404, detail="教材不存在")
    return {"message": "删除成功"}


@router.get("/conversations", response_model=List[ConversationResponse])
@limiter.limit("60/minute")
def get_conversations(request: Request, db: Session = Depends(get_db)):
    return ConversationService.get_all(db)


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
@limiter.limit("60/minute")
def get_conversation(request: Request, conversation_id: int, db: Session = Depends(get_db)):
    conversation = ConversationService.get_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    messages = MessageService.get_by_conversation(db, conversation_id)
    return {
        "id": conversation.id,
        "title": conversation.title,
        "character_id": conversation.character_id,
        "material_id": conversation.material_id,
        "teaching_mode": conversation.teaching_mode,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "character": conversation.character,
        "material": conversation.material,
        "messages": messages
    }


@router.post("/conversations", response_model=ConversationResponse)
@limiter.limit("30/minute")
def create_conversation(request: Request, conversation: ConversationCreate, db: Session = Depends(get_db)):
    return ConversationService.create(db, conversation)


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
@limiter.limit("30/minute")
def update_conversation(
    request: Request,
    conversation_id: int, 
    conversation: ConversationUpdate, 
    db: Session = Depends(get_db)
):
    updated = ConversationService.update(db, conversation_id, conversation)
    if not updated:
        raise HTTPException(status_code=404, detail="对话不存在")
    return updated


@router.delete("/conversations/{conversation_id}")
@limiter.limit("30/minute")
def delete_conversation(request: Request, conversation_id: int, db: Session = Depends(get_db)):
    if not ConversationService.delete(db, conversation_id):
        raise HTTPException(status_code=404, detail="对话不存在")
    return {"message": "删除成功"}


@router.get("/model-configs", response_model=List[ModelConfigResponse])
@limiter.limit("60/minute")
def get_model_configs(request: Request, db: Session = Depends(get_db)):
    return ModelConfigService.get_all(db)


@router.get("/model-configs/{config_id}", response_model=ModelConfigResponse)
@limiter.limit("60/minute")
def get_model_config(request: Request, config_id: int, db: Session = Depends(get_db)):
    config = ModelConfigService.get_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return config


@router.post("/model-configs", response_model=ModelConfigResponse)
@limiter.limit("20/minute")
def create_model_config(request: Request, config: ModelConfigCreate, db: Session = Depends(get_db)):
    return ModelConfigService.create(db, config)


@router.put("/model-configs/{config_id}", response_model=ModelConfigResponse)
@limiter.limit("20/minute")
def update_model_config(
    request: Request,
    config_id: int, 
    config: ModelConfigUpdate, 
    db: Session = Depends(get_db)
):
    updated = ModelConfigService.update(db, config_id, config)
    if not updated:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return updated


@router.delete("/model-configs/{config_id}")
@limiter.limit("20/minute")
def delete_model_config(request: Request, config_id: int, db: Session = Depends(get_db)):
    if not ModelConfigService.delete(db, config_id):
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return {"message": "删除成功"}


@router.get("/health")
@limiter.limit("60/minute")
def health_check(request: Request):
    return {"status": "ok", "message": "苏格拉底AI教学系统运行中"}
