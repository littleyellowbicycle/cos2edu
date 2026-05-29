import asyncio
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
import time
import uuid
import sys
import os
from pathlib import Path

from app.core.config import settings
from app.core.database import init_db
from app.core.limiter import limiter
from app.core.logging_config import setup_logging, get_logger
from app.core.static_files import setup_static_files, is_production_mode
from app.api import api_router
from app.api.v1.ws import set_narrative_engine
from app.graph.knowledge_graph import KnowledgeGraph
from app.engines.world_state_engine import WorldStateEngine
from app.engines.character_engine import CharacterEngine
from app.llm.context_budget import ContextBudget
from app.engines.teaching_engine import TeachingEngine
from app.engines.narrative_engine import NarrativeEngine
from app.engines.emotion_engine import EmotionEngine
from app.engines.event_engine import EventEngine
from app.engines.assessment_engine import AssessmentEngine
from app.state.state_manager import StateManager

logger = get_logger(__name__)

_narrative_engine = None
_state_manager = None
_emotion_engine = None
_event_engine = None
_state_task = None


def _get_content_dir() -> str:
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    content_dir = os.path.join(base, "content")
    if not os.path.exists(content_dir):
        content_dir = os.path.join(base, "backend", "content")
    return content_dir


def _init_engines():
    global _narrative_engine, _state_manager, _emotion_engine, _event_engine

    content_dir = _get_content_dir()
    logger.info(f"Loading content from: {content_dir}")

    kg = KnowledgeGraph()
    kg.load_from_yaml(os.path.join(content_dir, "modules"))

    world_engine = WorldStateEngine(content_dir)
    char_engine = CharacterEngine(content_dir)
    char_engine.load_characters()
    _emotion_engine = EmotionEngine(char_engine)
    _event_engine = EventEngine(content_dir)

    context_budget = ContextBudget()
    teaching_engine = TeachingEngine(kg, char_engine, context_budget)

    assessment_engine = AssessmentEngine(kg, char_engine)

    _state_manager = StateManager()

    _narrative_engine = NarrativeEngine(
        knowledge_graph=kg,
        world_state_engine=world_engine,
        character_engine=char_engine,
        teaching_engine=teaching_engine,
        state_manager=_state_manager,
        emotion_engine=_emotion_engine,
        event_engine=_event_engine,
        assessment_engine=assessment_engine,
    )

    set_narrative_engine(_narrative_engine)
    logger.info("NarrativeEngine initialized successfully")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _state_task

    setup_logging(level=settings.LOG_LEVEL)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Production mode: {is_production_mode()}")
    logger.info(f"Data directory: {settings.DATA_DIR}")
    logger.info(f"Database: {settings.DATABASE_URL}")

    await init_db()
    _init_engines()

    if _state_manager:
        _state_task = asyncio.create_task(_state_manager.start_periodic_flush())

    yield

    if _state_manager:
        await _state_manager.shutdown_flush()
    if _state_task:
        _state_task.cancel()
        try:
            await _state_task
        except asyncio.CancelledError:
            pass


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

    access_logger = get_logger("access")
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
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
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