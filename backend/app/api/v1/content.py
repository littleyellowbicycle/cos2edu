import os
import sys
import yaml
import json
import shutil
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from pydantic import BaseModel

from app.core.limiter import limiter
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _get_content_dir() -> str:
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    content_dir = os.path.join(base, "content")
    if not os.path.exists(content_dir):
        content_dir = os.path.join(base, "backend", "content")
    return content_dir


class YAMLContentRequest(BaseModel):
    content: str


class CharacterYAMLRequest(BaseModel):
    name: str
    teaching_style: str = ""
    personality: str = ""
    background: str = ""
    system_prompt_template: str = ""
    emotion_profile: Optional[dict] = None
    relationship_dynamics: Optional[dict] = None


class SearchRequest(BaseModel):
    keyword: str = ""
    character_id: Optional[int] = None
    limit: int = 50
    offset: int = 0


class MessageSearchRequest(BaseModel):
    query: str
    conversation_id: Optional[int] = None
    role: Optional[str] = None
    limit: int = 50
    offset: int = 0


@router.get("/conversations/search")
@limiter.limit("60/minute")
async def search_conversations(
    request: Request,
    keyword: str = "",
    character_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
):
    from app.repositories.unit_of_work import UnitOfWork
    from app.services import CharacterService

    async with UnitOfWork() as uow:
        conversations, total = await uow.conversations.search(
            keyword=keyword if keyword else None,
            character_id=character_id,
            skip=offset,
            limit=limit,
        )

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
            "character_name": char_name,
            "character_avatar": char_avatar,
            "character_avatar_type": char_avatar_type,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "message_count": len(conv.messages) if conv.messages else 0,
        })

    return {"total": total, "offset": offset, "limit": limit, "conversations": result}


@router.get("/conversations/{conversation_id}/messages/search")
@limiter.limit("60/minute")
async def search_messages(
    request: Request,
    conversation_id: int,
    q: str = "",
    role: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    from app.repositories.unit_of_work import UnitOfWork
    from app.repositories.message_search_repository import MessageSearchRepository
    from app.core.database import AsyncSessionLocal

    if not q:
        raise HTTPException(status_code=400, detail="搜索关键词不能为空")

    async with AsyncSessionLocal() as session:
        from app.repositories.conversation_repository import ConversationRepository
        conv_repo = ConversationRepository(session)
        conv = await conv_repo.get_by_id(conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="对话不存在")

        search_repo = MessageSearchRepository(session)
        messages, total = await search_repo.search_messages(
            query=q,
            conversation_id=conversation_id,
            role=role,
            skip=offset,
            limit=limit,
        )

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "messages": [
            {
                "id": m.id,
                "conversation_id": m.conversation_id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at,
            }
            for m in messages
        ],
    }


@router.get("/conversations/stats")
@limiter.limit("60/minute")
async def get_conversation_stats(request: Request):
    from app.repositories.unit_of_work import UnitOfWork
    from models.conversation import Conversation
    from models.message import Message
    from sqlalchemy import select, func

    async with UnitOfWork() as uow:
        total_conversations = await uow.session.execute(
            select(func.count(Conversation.id))
        )
        total_messages = await uow.session.execute(
            select(func.count(Message.id))
        )
        user_messages = await uow.session.execute(
            select(func.count(Message.id)).where(Message.role == "user")
        )
        assistant_messages = await uow.session.execute(
            select(func.count(Message.id)).where(Message.role == "assistant")
        )
        recent_conversations = await uow.session.execute(
            select(Conversation)
            .order_by(Conversation.updated_at.desc())
            .limit(5)
        )

    from app.services import CharacterService
    recent = []
    for conv in recent_conversations.scalars().all():
        char_name = None
        if conv.character_id:
            char = await CharacterService.get_by_id(conv.character_id)
            if char:
                char_name = char.name
        recent.append({
            "id": conv.id,
            "title": conv.title,
            "character_id": conv.character_id,
            "character_name": char_name,
            "updated_at": conv.updated_at,
        })

    return {
        "total_conversations": total_conversations.scalar() or 0,
        "total_messages": total_messages.scalar() or 0,
        "user_messages": user_messages.scalar() or 0,
        "assistant_messages": assistant_messages.scalar() or 0,
        "recent_conversations": recent,
    }


# ─── YAML Content Management ────────────────────────────────────

@router.get("/content/yaml/list")
@limiter.limit("60/minute")
async def list_yaml_files(request: Request):
    content_dir = _get_content_dir()
    files = []

    dirs_to_scan = [
        ("characters", "characters"),
        ("modules", "modules"),
        ("world", "world"),
    ]

    for subdir, label in dirs_to_scan:
        dir_path = os.path.join(content_dir, subdir)
        if os.path.isdir(dir_path):
            for fname in sorted(os.listdir(dir_path)):
                if fname.endswith(('.yaml', '.yml')):
                    fpath = os.path.join(dir_path, fname)
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                        files.append({
                            "path": f"{subdir}/{fname}",
                            "category": label,
                            "name": data.get("name", data.get("id", fname)) if data else fname,
                            "size": os.path.getsize(fpath),
                        })
                    except Exception:
                        files.append({
                            "path": f"{subdir}/{fname}",
                            "category": label,
                            "name": fname,
                            "size": os.path.getsize(fpath),
                        })

    syllabus_path = os.path.join(content_dir, "syllabus.yaml")
    if os.path.exists(syllabus_path):
        try:
            with open(syllabus_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            course = data.get("course", {}) if data else {}
            files.append({
                "path": "syllabus.yaml",
                "category": "syllabus",
                "name": course.get("name", "课程大纲"),
                "size": os.path.getsize(syllabus_path),
            })
        except Exception:
            files.append({
                "path": "syllabus.yaml",
                "category": "syllabus",
                "name": "课程大纲",
                "size": os.path.getsize(syllabus_path),
            })

    return {"files": files}


@router.get("/content/yaml/{file_path:path}")
@limiter.limit("60/minute")
async def read_yaml_file(request: Request, file_path: str):
    content_dir = _get_content_dir()
    full_path = os.path.join(content_dir, file_path)

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    if not os.path.abspath(full_path).startswith(os.path.abspath(content_dir)):
        raise HTTPException(status_code=403, detail="无权访问此路径")

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        data = yaml.safe_load(raw_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

    return {
        "path": file_path,
        "raw": raw_content,
        "parsed": data,
    }


@router.put("/content/yaml/{file_path:path}")
@limiter.limit("20/minute")
async def write_yaml_file(request: Request, file_path: str, body: YAMLContentRequest):
    content_dir = _get_content_dir()
    full_path = os.path.join(content_dir, file_path)

    if not os.path.abspath(full_path).startswith(os.path.abspath(content_dir)):
        raise HTTPException(status_code=403, detail="无权访问此路径")

    try:
        yaml.safe_load(body.content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML 语法错误: {str(e)}")

    backup_path = full_path + ".bak"
    if os.path.exists(full_path):
        shutil.copy2(full_path, backup_path)

    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(body.content)
    except Exception as e:
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, full_path)
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")

    return {"status": "ok", "message": "文件已保存", "path": file_path}


@router.post("/content/characters/create")
@limiter.limit("20/minute")
async def create_character_from_template(request: Request, body: CharacterYAMLRequest):
    content_dir = _get_content_dir()
    chars_dir = os.path.join(content_dir, "characters")
    os.makedirs(chars_dir, exist_ok=True)

    char_id = body.name.lower().replace(" ", "_").replace("（", "").replace("）", "")
    char_id = ''.join(c for c in char_id if c.isalnum() or c in ('_',))

    yaml_path = os.path.join(chars_dir, f"{char_id}.yaml")
    if os.path.exists(yaml_path):
        raise HTTPException(status_code=409, detail=f"角色 {char_id} 已存在")

    char_data = {
        "id": char_id,
        "name": body.name,
        "teaching_style": body.teaching_style,
        "personality": body.personality,
        "background": body.background,
        "system_prompt_template": body.system_prompt_template,
    }

    if body.emotion_profile:
        char_data["emotion_profile"] = body.emotion_profile
    else:
        char_data["emotion_profile"] = {
            "base_mood": 0.7,
            "mood_decay": 0.01,
            "event_sensitivity": {
                "student_correct": 0.06,
                "student_wrong": -0.01,
                "student_engaged": 0.10,
                "time_pressure": -0.05,
            },
        }

    if body.relationship_dynamics:
        char_data["relationship_dynamics"] = body.relationship_dynamics
    else:
        char_data["relationship_dynamics"] = {
            "trust_growth_rate": 0.015,
            "trust_decay_rate": 0.008,
            "max_trust": 1.0,
        }

    try:
        content = yaml.dump(char_data, allow_unicode=True, default_flow_style=False, sort_keys=False)
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建角色失败: {str(e)}")

    from app.main import _narrative_engine
    if _narrative_engine and _narrative_engine.characters:
        _narrative_engine.characters.load_characters()

    return {"status": "ok", "character_id": char_id, "path": f"characters/{char_id}.yaml"}


@router.get("/content/characters/templates")
@limiter.limit("60/minute")
async def get_character_templates(request: Request):
    templates = [
        {
            "id": "socratic",
            "name": "苏格拉底式",
            "teaching_style": "socratic",
            "personality": "善于提问引导，不直接给出答案，通过层层递进的问题帮助学生自行发现真理",
            "system_prompt_template": "你是一位苏格拉底式导师, 通过提问引导学生思考。\n- 不直接给出答案\n- 用反问法引导学生发现矛盾\n- 用反问鼓励自主思考",
        },
        {
            "id": "hands_on",
            "name": "实践型",
            "teaching_style": "hands_on_practice",
            "personality": "活泼好动，相信动手是最好的学习方式，先做再讲",
            "system_prompt_template": "你是一位实践型导师，相信做中学。\n- 先给出可运行代码\n- 在实验结果基础上解释原理\n- 鼓励修改参数观察变化",
        },
        {
            "id": "academic",
            "name": "学术型",
            "teaching_style": "academic_rigorous",
            "personality": "严谨认真，注重逻辑和推理，追求数学上的精确和完备",
            "system_prompt_template": "你是一位严谨的学术型导师。\n- 从定义和公理出发\n- 每步推理有据可查\n- 区分充分条件和必要条件",
        },
        {
            "id": "storytelling",
            "name": "故事型",
            "teaching_style": "storytelling",
            "personality": "善于用故事和类比解释抽象概念，让知识生动有趣",
            "system_prompt_template": "你是一位故事型导师，善于用叙事帮助理解。\n- 用寓言和类比解释概念\n- 构建场景让抽象变具体\n- 引导学生在故事中发现规律",
        },
    ]
    return {"templates": templates}


# ─── Hot Reload ──────────────────────────────────────────────────

@router.post("/content/reload")
@limiter.limit("10/minute")
async def reload_content(request: Request):
    from app.main import _narrative_engine

    if not _narrative_engine:
        raise HTTPException(status_code=503, detail="叙事引擎未初始化")

    content_dir = _get_content_dir()

    _narrative_engine.graph.load_from_yaml(os.path.join(content_dir, "modules"))
    _narrative_engine.characters.load_characters()
    _narrative_engine.world.reload(os.path.join(content_dir, "world"))
    if _narrative_engine.emotion:
        _narrative_engine.emotion.reload(_narrative_engine.characters)
    if _narrative_engine.events:
        _narrative_engine.events.reload(os.path.join(content_dir, "world"))

    logger.info("Content YAML hot-reloaded successfully")

    return {
        "status": "ok",
        "message": "所有内容已热重载",
        "knowledge_points": len(_narrative_engine.graph.get_all_points()),
        "characters": len(_narrative_engine.characters.get_all_characters()),
        "scenes": len(_narrative_engine.world.get_all_scenes()),
    }