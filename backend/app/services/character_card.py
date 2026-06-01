import base64
import io
import json
import os
import uuid
from typing import Optional

from PIL import Image
from PIL.PngImagePlugin import PngInfo
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging_config import get_logger
from app.services.crud_services import CharacterService
from app.schemas import CharacterCreate

logger = get_logger(__name__)

ST_SPEC_V2 = "chara_card_v2"
ST_SPEC_V3 = "chara_card_v3"


class STCharacterData(BaseModel):
    name: str = ""
    description: str = ""
    personality: str = ""
    scenario: str = ""
    first_mes: str = ""
    mes_example: str = ""
    system_prompt: str = ""
    post_history_instructions: str = ""
    tags: list[str] = Field(default_factory=list)
    creator: str = ""
    character_version: str = ""
    alternate_greetings: list[str] = Field(default_factory=list)
    extensions: dict = Field(default_factory=dict)
    character_book: Optional[dict] = None


class STCharacterCardV2(BaseModel):
    spec: str = ST_SPEC_V2
    spec_version: str = "2.0"
    data: STCharacterData


class STCharacterCardV3(BaseModel):
    spec: str = ST_SPEC_V3
    spec_version: str = "3.0"
    data: STCharacterData


def _cos2edu_to_st_data(character_dict: dict) -> STCharacterData:
    return STCharacterData(
        name=character_dict.get("name", ""),
        description=character_dict.get("background", "") or character_dict.get("description", ""),
        personality=character_dict.get("personality", ""),
        scenario="",
        first_mes="",
        mes_example="",
        system_prompt="",
        post_history_instructions="",
        tags=["cos2edu", "education"],
        creator="Cos2Edu",
        character_version="1.0",
        alternate_greetings=[],
        extensions={
            "cos2edu_avatar_type": character_dict.get("avatar_type", "emoji"),
            "cos2edu_avatar": character_dict.get("avatar", ""),
            "cos2edu_description": character_dict.get("description", ""),
        },
    )


def _st_data_to_cos2edu(data: STCharacterData) -> dict:
    extensions = data.extensions or {}
    description = extensions.get("cos2edu_description", "")
    if not description and data.description:
        description = data.description[:500] if len(data.description) > 500 else data.description

    background = data.description
    if extensions.get("cos2edu_description") and data.description:
        background = data.description

    avatar_type = extensions.get("cos2edu_avatar_type", "emoji")
    avatar = extensions.get("cos2edu_avatar", "")

    return {
        "name": data.name or "Unnamed",
        "description": description,
        "personality": data.personality or "善良且乐于助人",
        "background": background,
        "avatar_type": avatar_type,
        "avatar": avatar,
        "_st_first_mes": data.first_mes,
        "_st_scenario": data.scenario,
        "_st_mes_example": data.mes_example,
        "_st_system_prompt": data.system_prompt,
        "_st_post_history_instructions": data.post_history_instructions,
        "_st_tags": data.tags,
        "_st_alternate_greetings": data.alternate_greetings,
        "_st_character_book": data.character_book,
    }


async def export_character_card(character_id: int) -> bytes:
    character = await CharacterService.get_by_id(character_id)
    if not character:
        raise ValueError("角色不存在")

    char_dict = {
        "name": character.name,
        "description": character.description,
        "personality": character.personality,
        "background": character.background,
        "avatar": character.avatar,
        "avatar_type": character.avatar_type,
    }

    st_data = _cos2edu_to_st_data(char_dict)
    card = STCharacterCardV2(data=st_data)
    card_json = card.model_dump_json()

    png_info = PngInfo()
    png_info.add_text("chara", base64.b64encode(card_json.encode("utf-8")).decode("ascii"))

    if character.avatar_type == "image" and character.avatar:
        avatar_path = os.path.join(settings.AVATARS_DIR, character.avatar)
        if os.path.exists(avatar_path):
            img = Image.open(avatar_path)
            if img.mode == "RGBA":
                pass
            elif img.mode == "P":
                img = img.convert("RGBA")
            else:
                img = img.convert("RGBA")
        else:
            img = _create_default_avatar(character.name)
    else:
        img = _create_default_avatar(character.name)

    buf = io.BytesIO()
    img.save(buf, format="PNG", pnginfo=png_info)
    buf.seek(0)
    return buf.getvalue()


async def import_character_card(png_bytes: bytes) -> dict:
    buf = io.BytesIO(png_bytes)
    img = Image.open(buf)

    metadata = img.info

    raw_data = metadata.get("ccv3") or metadata.get("chara")
    if not raw_data:
        raise ValueError("PNG 文件中未找到 SillyTavern 角色卡数据（缺少 chara 或 ccv3 元数据块）")

    try:
        json_str = base64.b64decode(raw_data).decode("utf-8")
        card_json = json.loads(json_str)
    except Exception as e:
        raise ValueError(f"角色卡数据解析失败: {str(e)}")

    data_dict = card_json.get("data", card_json)
    st_data = STCharacterData(**data_dict)
    cos2edu_data = _st_data_to_cos2edu(st_data)

    avatar_type = cos2edu_data.pop("avatar_type")
    avatar = cos2edu_data.pop("avatar")

    if avatar_type == "image" and not avatar:
        avatar_filename = f"{uuid.uuid4().hex}.png"
        avatar_path = os.path.join(settings.AVATARS_DIR, avatar_filename)
        os.makedirs(settings.AVATARS_DIR, exist_ok=True)
        save_img = img.copy()
        if save_img.mode != "RGBA":
            save_img = save_img.convert("RGBA")
        save_img.save(avatar_path, format="PNG")
        avatar = avatar_filename
        avatar_type = "image"

    character_create = CharacterCreate(
        name=cos2edu_data["name"],
        description=cos2edu_data.get("description"),
        personality=cos2edu_data.get("personality", "善良且乐于助人"),
        background=cos2edu_data.get("background"),
        avatar_type=avatar_type,
        avatar=avatar,
    )

    created = await CharacterService.create(character_create)

    st_extra = {}
    for key, value in cos2edu_data.items():
        if key.startswith("_st_"):
            st_extra[key[4:]] = value

    return {
        "character": {
            "id": created.id,
            "name": created.name,
            "description": created.description,
            "personality": created.personality,
            "background": created.background,
            "avatar": created.avatar,
            "avatar_type": created.avatar_type,
            "is_active": created.is_active,
            "created_at": created.created_at.isoformat() if created.created_at else None,
            "updated_at": created.updated_at.isoformat() if created.updated_at else None,
        },
        "imported_fields": {
            "first_mes": st_extra.get("first_mes", ""),
            "scenario": st_extra.get("scenario", ""),
            "mes_example": st_extra.get("mes_example", ""),
            "system_prompt": st_extra.get("system_prompt", ""),
            "post_history_instructions": st_extra.get("post_history_instructions", ""),
            "tags": st_extra.get("tags", []),
            "alternate_greetings": st_extra.get("alternate_greetings", []),
            "character_book": st_extra.get("character_book"),
        },
        "missing_fields": _get_missing_fields(st_data),
    }


def _get_missing_fields(st_data: STCharacterData) -> list[str]:
    missing = []
    if not st_data.first_mes:
        missing.append("first_mes (开场白)")
    if not st_data.mes_example:
        missing.append("mes_example (对话示例)")
    if not st_data.scenario:
        missing.append("scenario (场景设定)")
    if not st_data.system_prompt:
        missing.append("system_prompt (系统提示)")
    if not st_data.character_book:
        missing.append("character_book (角色知识库)")
    if not st_data.tags:
        missing.append("tags (标签)")
    if not st_data.alternate_greetings:
        missing.append("alternate_greetings (备选开场白)")
    if not st_data.post_history_instructions:
        missing.append("post_history_instructions (历史后指令)")
    return missing


def _create_default_avatar(name: str) -> Image.Image:
    img = Image.new("RGBA", (256, 256), (74, 144, 217, 255))
    return img
