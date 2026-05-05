from fastapi import APIRouter

router = APIRouter()


@router.get("/pages/health")
async def get_pages_health():
    return {"status": "ok", "module": "pages"}