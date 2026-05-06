import os
from pydantic_settings import BaseSettings
from typing import Optional, List, Literal
from pydantic import field_validator


EnvironmentType = Literal["dev", "prod", "test"]


class BaseConfig(BaseSettings):
    APP_NAME: str = "苏格拉底AI教学系统"
    APP_VERSION: str = "1.0.0"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    DATA_DIR: str = "./data"
    CHARACTERS_DIR: str = "./data/characters"
    MATERIALS_DIR: str = "./data/materials"
    CONVERSATIONS_DIR: str = "./data/conversations"
    UPLOADS_DIR: str = "./data/uploads"
    AVATARS_DIR: str = "./data/uploads/avatars"
    BACKGROUNDS_DIR: str = "./data/uploads/backgrounds"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
    
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    
    DEFAULT_MODEL: str = "gpt-4o"
    DEFAULT_PROVIDER: str = "openai"
    
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    
    ANTHROPIC_API_KEY: Optional[str] = None
    
    DASHSCOPE_API_KEY: Optional[str] = None
    ZHIPU_API_KEY: Optional[str] = None
    
    DOUBAO_API_KEY: Optional[str] = None
    DOUBAO_BASE_URL: Optional[str] = None
    
    WENXIN_API_KEY: Optional[str] = None
    WENXIN_BASE_URL: Optional[str] = None
    
    HUNYUAN_API_KEY: Optional[str] = None
    HUNYUAN_BASE_URL: Optional[str] = None
    
    MOONSHOT_API_KEY: Optional[str] = None
    MOONSHOT_BASE_URL: Optional[str] = None
    
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_BASE_URL: Optional[str] = None
    
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    RATE_LIMIT_STORAGE: str = "memory"
    
    MAX_HISTORY_MESSAGES: int = 20
    MAX_HISTORY_TOKENS: int = 4000
    TOKEN_ESTIMATION_RATIO: float = 1.3
    
    USE_TIKTOKEN: bool = True
    TIKTOKEN_DEFAULT_MODEL: str = "gpt-4"
    
    ENABLE_HISTORY_SUMMARY: bool = False
    SUMMARY_MAX_TOKENS: int = 500
    SUMMARY_TEMPERATURE: float = 0.3
    
    SUMMARY_UPDATE_STRATEGY: str = "auto"
    SUMMARY_AUTO_THRESHOLD: float = 0.3
    
    MAX_HISTORY_MESSAGES_VIP: int = 50
    MAX_HISTORY_TOKENS_VIP: int = 8000
    
    CORS_ALLOW_ORIGINS: List[str] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"
    
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    @field_validator("CORS_ALLOW_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    class Config:
        case_sensitive = True
        extra = "ignore"


class DevConfig(BaseConfig):
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    CORS_ALLOW_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    CORS_ALLOW_METHODS: List[str] = ["*"]
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"


class ProdConfig(BaseConfig):
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"


class TestConfig(BaseConfig):
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    CORS_ALLOW_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_METHODS: List[str] = ["*"]
    
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    
    class Config:
        env_file = ".env.test"
        case_sensitive = True
        extra = "ignore"


def get_settings() -> BaseConfig:
    env: EnvironmentType = os.getenv("APP_ENV", "dev").lower()
    
    if env == "prod":
        return ProdConfig()
    elif env == "test":
        return TestConfig()
    else:
        return DevConfig()


settings = get_settings()


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
