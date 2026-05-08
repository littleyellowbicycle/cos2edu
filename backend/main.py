from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
import time
import uuid
import sys
import os

from app.core.config import settings
from app.core.database import init_db
from app.core.limiter import limiter
from app.core.logging_config import setup_logging, get_logger
from app.core.static_files import setup_static_files, is_production_mode
from app.api import api_router

logger = get_logger(__name__)
access_logger = get_logger("access")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(level=settings.LOG_LEVEL)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Production mode: {is_production_mode()}")
    logger.info(f"Data directory: {settings.DATA_DIR}")
    logger.info(f"Database: {settings.DATABASE_URL}")
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.state.limiter = limiter


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    start_time = time.perf_counter()
    client_ip = get_client_ip(request)
    method = request.method
    path = request.url.path
    query_string = request.url.query
    full_path = f"{path}?{query_string}" if query_string else path

    access_logger.info(
        f"[{request_id}] REQUEST - {client_ip} - {method} {full_path} - "
        f"User-Agent: {request.headers.get('user-agent', 'N/A')}"
    )

    try:
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000

        access_logger.info(
            f"[{request_id}] RESPONSE - {client_ip} - {method} {full_path} - "
            f"Status: {response.status_code} - Duration: {process_time:.2f}ms"
        )

        return response
    except Exception as e:
        process_time = (time.perf_counter() - start_time) * 1000
        access_logger.error(
            f"[{request_id}] ERROR - {client_ip} - {method} {full_path} - "
            f"Error: {type(e).__name__}: {str(e)} - Duration: {process_time:.2f}ms",
            exc_info=True
        )
        raise


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        return x_real_ip

    if request.client:
        return request.client.host
    return "unknown"


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_M_MANY_REQUESTS,
        content={
            "detail": "请求过于频繁，请稍后再试",
            "retry_after": str(exc.headers.get("Retry-After", "60"))
        }
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.include_router(api_router, prefix="/api/v1", tags=["api-v1"])

setup_static_files(app)

if settings.DEBUG:
    @app.get("/")
    async def root():
        return {"message": "API is running", "docs": "/docs"}


@app.get("/health")
@limiter.limit("60/minute")
async def health(request: Request):
    return {"status": "ok", "name": settings.APP_NAME, "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )