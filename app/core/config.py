import os
from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import field_validator


class Settings(BaseSettings):
    # 应用基础配置
    APP_NAME: str = "苏格拉底AI教学系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS 配置
    # 注意：allow_origins=["*"] 不能与 allow_credentials=True 同时使用
    CORS_ALLOW_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    @field_validator("CORS_ALLOW_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/app.db"
    
    # 数据目录
    DATA_DIR: str = "./data"
    CHARACTERS_DIR: str = "./data/characters"
    MATERIALS_DIR: str = "./data/materials"
    CONVERSATIONS_DIR: str = "./data/conversations"
    UPLOADS_DIR: str = "./data/uploads"
    AVATARS_DIR: str = "./data/uploads/avatars"
    BACKGROUNDS_DIR: str = "./data/uploads/backgrounds"
    
    # 上传配置
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    
    # 模型配置
    DEFAULT_MODEL: str = "gpt-4o"
    DEFAULT_PROVIDER: str = "openai"
    
    # OpenAI配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    
    # Anthropic配置
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # 国内模型配置（示例）
    DASHSCOPE_API_KEY: Optional[str] = None  # 阿里通义千问
    ZHIPU_API_KEY: Optional[str] = None       # 智谱AI
    
    # 字节跳动豆包
    DOUBAO_API_KEY: Optional[str] = None
    DOUBAO_BASE_URL: Optional[str] = None
    
    # 百度文心一言
    WENXIN_API_KEY: Optional[str] = None
    WENXIN_BASE_URL: Optional[str] = None
    
    # 腾讯混元
    HUNYUAN_API_KEY: Optional[str] = None
    HUNYUAN_BASE_URL: Optional[str] = None
    
    # 月之暗面 Moonshot (Kimi)
    MOONSHOT_API_KEY: Optional[str] = None
    MOONSHOT_BASE_URL: Optional[str] = None
    
    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_BASE_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# 确保必要的目录存在
for dir_path in [
    settings.DATA_DIR,
    settings.CHARACTERS_DIR,
    settings.MATERIALS_DIR,
    settings.CONVERSATIONS_DIR,
    settings.UPLOADS_DIR,
    settings.AVATARS_DIR,
    settings.BACKGROUNDS_DIR,
]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
