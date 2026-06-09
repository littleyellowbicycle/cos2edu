import os
import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException
from app.core.config import settings


class FileUploadService:
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    CHUNK_SIZE = 64 * 1024  # 64KB chunks
    
    @staticmethod
    def _get_file_extension(filename: str) -> str:
        return os.path.splitext(filename)[1].lower()
    
    @staticmethod
    def _generate_unique_filename(extension: str) -> str:
        return f"{uuid.uuid4().hex}{extension}"
    
    @staticmethod
    def _validate_image(file: UploadFile) -> None:
        if not file.content_type:
            raise HTTPException(status_code=400, detail="无法识别文件类型")
        
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的图片类型: {file.content_type}。支持的类型: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
            )
    
    @staticmethod
    async def _save_file_with_size_check(file: UploadFile, filepath: str) -> None:
        total_size = 0
        try:
            with open(filepath, "wb") as f:
                while True:
                    chunk = await file.read(FileUploadService.CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    total_size += len(chunk)
                    if total_size > settings.MAX_UPLOAD_SIZE:
                        f.close()
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        raise HTTPException(
                            status_code=400,
                            detail=f"文件大小超过限制。最大允许: {settings.MAX_UPLOAD_SIZE // 1024 // 1024} MB"
                        )
                    
                    f.write(chunk)
        except Exception as e:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    @staticmethod
    async def save_avatar(file: UploadFile) -> str:
        FileUploadService._validate_image(file)
        
        extension = FileUploadService._get_file_extension(file.filename or "")
        if extension not in FileUploadService.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件扩展名: {extension}。支持的扩展名: {', '.join(FileUploadService.ALLOWED_EXTENSIONS)}"
            )
        
        filename = FileUploadService._generate_unique_filename(extension)
        filepath = os.path.join(settings.AVATARS_DIR, filename)
        
        await FileUploadService._save_file_with_size_check(file, filepath)
        
        return f"/api/uploads/avatars/{filename}"
    
    @staticmethod
    async def save_background(file: UploadFile) -> str:
        FileUploadService._validate_image(file)
        
        extension = FileUploadService._get_file_extension(file.filename or "")
        if extension not in FileUploadService.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件扩展名: {extension}。支持的扩展名: {', '.join(FileUploadService.ALLOWED_EXTENSIONS)}"
            )
        
        filename = FileUploadService._generate_unique_filename(extension)
        filepath = os.path.join(settings.BACKGROUNDS_DIR, filename)
        
        await FileUploadService._save_file_with_size_check(file, filepath)
        
        return f"/api/uploads/backgrounds/{filename}"
    
    @staticmethod
    def delete_file(file_url: str) -> bool:
        try:
            if file_url.startswith("/api/uploads/"):
                relative_path = file_url.replace("/api/uploads/", "")
                filepath = os.path.realpath(os.path.join(settings.UPLOADS_DIR, relative_path))
                if not filepath.startswith(os.path.realpath(settings.UPLOADS_DIR)):
                    return False
                if os.path.exists(filepath):
                    os.remove(filepath)
                    return True
            return False
        except OSError:
            return False
