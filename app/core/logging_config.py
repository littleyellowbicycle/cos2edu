import logging
import sys
from typing import Optional
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from app.core.config import settings


def ensure_logs_dir() -> Path:
    logs_dir = Path(settings.DATA_DIR) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def setup_logging(
    level: Optional[str] = None,
    format_string: Optional[str] = None,
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    配置应用日志系统，支持控制台和文件双重输出
    
    Args:
        level: 日志级别，默认从 settings.DEBUG 推断
        format_string: 日志格式字符串
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
    
    Returns:
        配置好的根 logger
    """
    if level is None:
        level = "DEBUG" if settings.DEBUG else "INFO"
    
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    simple_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    if file_output:
        logs_dir = ensure_logs_dir()
        
        app_log_file = logs_dir / "app.log"
        app_handler = RotatingFileHandler(
            app_log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        app_handler.setLevel(numeric_level)
        app_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(app_handler)
        
        error_log_file = logs_dir / "error.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
        
        access_log_file = logs_dir / "access.log"
        access_handler = TimedRotatingFileHandler(
            access_log_file,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8"
        )
        access_handler.setLevel(logging.INFO)
        access_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(access_handler)
    
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(numeric_level)
    
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(logging.WARNING)
    
    sqlalchemy_logger = logging.getLogger("sqlalchemy")
    sqlalchemy_logger.setLevel(logging.WARNING)
    
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.WARNING)
    
    httpcore_logger = logging.getLogger("httpcore")
    httpcore_logger.setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的 logger
    
    Args:
        name: logger 名称，通常使用 __name__
    
    Returns:
        配置好的 logger 实例
    """
    return logging.getLogger(name)


def setup_cli_logging(level: str = "INFO") -> logging.Logger:
    """
    为命令行脚本配置简单的日志（仅控制台输出）
    
    Args:
        level: 日志级别
    
    Returns:
        配置好的根 logger
    """
    return setup_logging(level=level, file_output=False)


def get_logs_dir() -> Path:
    """
    获取日志目录路径
    
    Returns:
        日志目录的 Path 对象
    """
    return ensure_logs_dir()
