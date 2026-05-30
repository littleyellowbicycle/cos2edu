from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import text, inspect
from app.core.config import settings
from models.base import Base
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _is_sqlite() -> bool:
    return settings.DATABASE_URL.startswith("sqlite")


_engine_kwargs = {"connect_args": {"check_same_thread": False, "timeout": 5}} if _is_sqlite() else {
    "poolclass": QueuePool,
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
}

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


_MIGRATIONS = [
    ("materials", [
        ("status", "VARCHAR(20) DEFAULT 'parsing'"),
        ("error_code", "VARCHAR(50)"),
        ("review_status", "VARCHAR(20)"),
        ("source_syllabus_id", "INTEGER"),
        ("page_count", "INTEGER"),
        ("char_count", "INTEGER"),
    ]),
    ("conversations", [
        ("knowledge_point_id", "VARCHAR(100)"),
        ("scene_id", "VARCHAR(50)"),
        ("narrative_context", "TEXT"),
        ("summary", "TEXT"),
        ("summary_covered_message_count", "INTEGER DEFAULT 0"),
        ("summary_created_at", "DATETIME"),
        ("summary_updated_at", "DATETIME"),
    ]),
    ("world_state", [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("current_day", "INTEGER DEFAULT 1"),
        ("current_scene", "VARCHAR(50) DEFAULT 'classroom'"),
        ("narrative_phase", "VARCHAR(50) DEFAULT 'prologue'"),
        ("global_flags", "TEXT"),
        ("updated_at", "DATETIME"),
    ]),
    ("character_state", [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("character_id", "INTEGER"),
        ("current_mood", "FLOAT DEFAULT 0.7"),
        ("trust_level", "FLOAT DEFAULT 0.5"),
        ("updated_at", "DATETIME"),
    ]),
    ("learning_progress", [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("knowledge_point_id", "VARCHAR(100)"),
        ("mastery_level", "FLOAT DEFAULT 0"),
        ("status", "VARCHAR(20) DEFAULT 'locked'"),
        ("attempts", "INTEGER DEFAULT 0"),
        ("weak_areas", "TEXT"),
        ("last_reviewed_at", "DATETIME"),
        ("created_at", "DATETIME"),
        ("updated_at", "DATETIME"),
    ]),
    ("event_log", [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("event_type", "VARCHAR(50)"),
        ("event_id", "VARCHAR(100)"),
        ("data", "TEXT"),
        ("created_at", "DATETIME"),
    ]),
    ("syllabuses", [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("material_id", "INTEGER"),
        ("name", "VARCHAR(200)"),
        ("total_days", "INTEGER"),
        ("content", "TEXT"),
        ("review_status", "VARCHAR(20) DEFAULT 'pending'"),
        ("created_at", "DATETIME"),
        ("updated_at", "DATETIME"),
    ]),
]


async def _run_migrations(conn) -> None:
    for table_name, columns in _MIGRATIONS:
        try:
            result = await conn.execute(text(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            ))
            if not result.fetchone():
                continue

            col_result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
            existing_cols = {row[1] for row in col_result.fetchall()}

            for col_name, col_type in columns:
                if col_name not in existing_cols:
                    await conn.execute(text(
                        f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                    ))
                    logger.info(f"Migration: added {table_name}.{col_name}")
        except Exception as e:
            logger.warning(f"Migration for {table_name} skipped: {e}")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _run_migrations(conn)
    logger.info("Database initialized (tables created, migrations applied)")


async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
