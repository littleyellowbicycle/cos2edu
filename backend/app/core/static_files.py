import os
import sys
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException


def get_static_dir() -> str:
    """获取静态文件目录（兼容打包模式）"""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "static")
    
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    frontend_dir = os.path.dirname(backend_dir)
    static_dir = os.path.join(frontend_dir, "static")
    
    if os.path.exists(static_dir):
        return static_dir
    
    dist_dir = os.path.join(frontend_dir, "frontend", "dist")
    if os.path.exists(dist_dir):
        return dist_dir
    
    return os.path.join(backend_dir, "static")


def setup_static_files(app):
    """配置静态文件托管"""
    static_dir = get_static_dir()
    
    if not os.path.exists(static_dir):
        return False
    
    index_path = os.path.join(static_dir, "index.html")
    if not os.path.exists(index_path):
        index_path = os.path.join(static_dir, "dist", "index.html")
    
    if not os.path.exists(index_path):
        return False
    
    assets_dir = os.path.join(static_dir, "assets")
    dist_assets = os.path.join(static_dir, "dist", "assets")
    
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    elif os.path.exists(dist_assets):
        app.mount("/assets", StaticFiles(directory=dist_assets), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        dist_index = os.path.join(static_dir, "dist", "index.html")
        if os.path.exists(dist_index):
            return FileResponse(dist_index)
        
        return FileResponse(index_path)
    
    return True


def is_production_mode() -> bool:
    """判断是否为生产模式（打包后）"""
    return getattr(sys, 'frozen', False)