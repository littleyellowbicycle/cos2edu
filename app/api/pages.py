from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter()

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")


@router.get("/")
async def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@router.get("/chat")
async def chat_page():
    return FileResponse(os.path.join(STATIC_DIR, "chat.html"))


@router.get("/characters")
async def characters_page():
    return FileResponse(os.path.join(STATIC_DIR, "characters.html"))


@router.get("/materials")
async def materials_page():
    return FileResponse(os.path.join(STATIC_DIR, "materials.html"))


@router.get("/settings")
async def settings_page():
    return FileResponse(os.path.join(STATIC_DIR, "settings.html"))


@router.get("/backgrounds")
async def backgrounds_page():
    return FileResponse(os.path.join(STATIC_DIR, "backgrounds.html"))
