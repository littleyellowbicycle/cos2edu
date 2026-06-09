import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO"):
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Don't clear handlers — that would remove uvicorn's own handlers.
    # if root_logger.handlers:
    #     root_logger.handlers.clear()
    
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)
    
    access_logger = logging.getLogger("access")
    access_logger.setLevel(log_level)
    if not access_logger.handlers:
        access_handler = logging.StreamHandler(sys.stdout)
        access_handler.setLevel(log_level)
        access_handler.setFormatter(formatter)
        access_logger.addHandler(access_handler)
        access_logger.propagate = False


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name)
