from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.core.database import SessionLocal
from app.core.config import settings
from app.core.limiter import limiter
from app.services import FileUploadService, BackgroundConfigService
from app.schemas import (
    BackgroundConfigCreate, BackgroundConfigUpdate, BackgroundConfigResponse
)


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload/avatar")
@limiter.limit("10/minute")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        file_url = await FileUploadService.save_avatar(file)
        return {"url": file_url, "message": "上传成功"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/upload/background")
@limiter.limit("10/minute")
async def upload_background(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        file_url = await FileUploadService.save_background(file)
        return {"url": file_url, "message": "上传成功"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/uploads/avatars/{filename}")
@limiter.limit("60/minute")
async def get_avatar(request: Request, filename: str):
    filepath = os.path.join(settings.AVATARS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(filepath)


@router.get("/uploads/backgrounds/{filename}")
@limiter.limit("60/minute")
async def get_background(request: Request, filename: str):
    filepath = os.path.join(settings.BACKGROUNDS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(filepath)


@router.get("/backgrounds", response_model=list[BackgroundConfigResponse])
@limiter.limit("60/minute")
def get_backgrounds(request: Request, db: Session = Depends(get_db)):
    return BackgroundConfigService.get_all(db)


@router.get("/backgrounds/default")
@limiter.limit("60/minute")
def get_default_background(request: Request, db: Session = Depends(get_db)):
    bg = BackgroundConfigService.get_default(db)
    if bg:
        return bg
    return {
        "id": 0,
        "name": "默认浅灰",
        "background_type": "color",
        "background_value": "#f9fafb",
        "is_active": True,
        "is_default": True
    }


@router.get("/backgrounds/{bg_id}", response_model=BackgroundConfigResponse)
@limiter.limit("60/minute")
def get_background(request: Request, bg_id: int, db: Session = Depends(get_db)):
    bg = BackgroundConfigService.get_by_id(db, bg_id)
    if not bg:
        raise HTTPException(status_code=404, detail="背景配置不存在")
    return bg


@router.post("/backgrounds", response_model=BackgroundConfigResponse)
@limiter.limit("20/minute")
def create_background(
    request: Request,
    config: BackgroundConfigCreate,
    db: Session = Depends(get_db)
):
    return BackgroundConfigService.create(db, config)


@router.put("/backgrounds/{bg_id}", response_model=BackgroundConfigResponse)
@limiter.limit("20/minute")
def update_background(
    request: Request,
    bg_id: int,
    config: BackgroundConfigUpdate,
    db: Session = Depends(get_db)
):
    updated = BackgroundConfigService.update(db, bg_id, config)
    if not updated:
        raise HTTPException(status_code=404, detail="背景配置不存在")
    return updated


@router.delete("/backgrounds/{bg_id}")
@limiter.limit("20/minute")
def delete_background(request: Request, bg_id: int, db: Session = Depends(get_db)):
    bg = BackgroundConfigService.get_by_id(db, bg_id)
    if bg and bg.background_type == "image":
        FileUploadService.delete_file(bg.background_value)
    
    if not BackgroundConfigService.delete(db, bg_id):
        raise HTTPException(status_code=404, detail="背景配置不存在")
    return {"message": "删除成功"}
