# 苏格拉底AI教学系统 - 前后端分离架构方案

## 一、现状分析

### 1.1 当前架构

当前项目采用 **单体架构**，前后端代码混合部署：

```
cos2edu/
├── app/                    # 后端 Python 代码
│   ├── api/               # API 路由
│   ├── core/              # 核心配置
│   ├── schemas/           # 数据模型
│   └── services/          # 业务逻辑
├── static/                # 前端静态文件（HTML/JS/CSS）
└── main.py               # 应用入口（同时提供API和静态资源）
```

### 1.2 耦合问题分析

| 问题类型 | 具体表现 | 影响 |
|---------|---------|------|
| **部署耦合** | 前端静态文件与后端服务绑定 | 无法独立部署、扩缩容困难 |
| **开发耦合** | 前后端代码在同一仓库 | 开发流程冲突、技术栈受限 |
| **技术栈耦合** | 前端使用原生JS | 缺乏现代化开发工具、代码可维护性差 |
| **架构耦合** | FastAPI同时处理页面路由和API | 职责不清、测试复杂度高 |
| **数据层耦合** | 模型与数据库连接紧耦合 | 难以测试、难以切换数据库 |

### 1.3 当前API设计评估

当前已具备良好的 RESTful API 基础：
- `/api/characters` - 角色管理
- `/api/materials` - 教材管理
- `/api/conversations` - 对话管理
- `/api/chat/{id}/stream` - 流式聊天

---

## 二、前后端分离方案（MVP）

### 2.1 目标架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        客户端层                                        │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐            │
│   │   Web 浏览器  │  │   移动端App   │  │    第三方集成     │            │
│   │  (Vue 3)     │  │   (H5/Web)    │  │    (API调用)     │            │
│   └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘            │
└──────────┼─────────────────┼───────────────────┼───────────────────────┘
           │                 │                   │
           ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        网关层 (Nginx)                                  │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  /          → 前端静态资源 (dist/)                               │  │
│   │  /api/      → 反向代理到 backend:8000                           │  │
│   │  /uploads/  → 静态文件服务 (共享目录)                            │  │
│   └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
          ┌──────────────────────────┼──────────────────────────┐
          ▼                          ▼                          ▼
┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
│   前端容器         │      │     后端服务        │      │     数据层        │
│   (Nginx)         │      │   (FastAPI)       │      │                   │
├───────────────────┤      ├───────────────────┤      ├───────────────────┤
│ /usr/share/nginx/│      │ /app/main.py      │      │ PostgreSQL/SQLite │
│   html/dist/     │      │ /app/app/         │      │ (对话/角色/教材)   │
└───────────────────┘      │ /shared/data/    │      ├───────────────────┤
                           │                  │      │ Redis             │
                           └───────────────────┘      │ (缓存/会话/限流)   │
                                                      └───────────────────┘
                                    │
                                    ▼
                           ┌───────────────────┐
                           │   共享存储         │
                           │ /shared/data/     │
                           │ (上传文件/配置)    │
                           └───────────────────┘
```

### 2.2 技术选型

| 层级 | 技术 | 版本 | 选型理由 | MVP必要性 |
|-----|------|------|---------|-----------|
| 前端框架 | Vue | 3.4+ | 轻量、响应式、生态成熟 | **必须** |
| 构建工具 | Vite | 6.5+ | 快速开发、热更新、Rollup优化 | **必须** |
| UI组件 | Element Plus | 2.8+ | Vue 3 原生支持、中文文档完善 | **必须** |
| 状态管理 | Pinia | 2.2+ | Vue 官方推荐、轻量高效 | **推荐** |
| HTTP客户端 | Axios | 1.6+ | 成熟稳定、拦截器支持完善 | **必须** |
| 后端框架 | FastAPI | 0.110+ | 高性能、类型安全、自动文档 | **必须** |
| 数据库 | SQLite/PostgreSQL | - | SQLite开发/测试，PostgreSQL生产 | **必须** |
| 缓存 | Redis | 7+ | 会话管理、限流、缓存（可选，MVP 可用内存存储） | **可选** |
| 网关 | Nginx | 1.25+ | 反向代理、静态资源、负载均衡 | **必须** |

---

## 三、数据流图

### 3.1 完整数据流

```
[前端请求] → [Nginx代理] → [后端API] → [Service层] → [Repository层] → [数据库/缓存]
     ↑                                                                 │
     └──────────────────────────────────────────────────────────────────┘
```

### 3.2 详细数据流示例

#### 场景1：用户发送聊天消息

```
1. 前端 Chat.vue
    │
    ▼ POST /api/v1/chat/{id}/stream
2. Nginx (反向代理)
    │
    ▼ proxy_pass http://backend:8000/api/v1/chat/{id}/stream
3. FastAPI - app/api/v1/chat.py
    │
    ▼ 调用 TeachingService.generate_response()
4. services/teaching_service.py
    │
    ▼ 通过 UnitOfWork 获取 Repository
    │
    ▼ [可选] 检查 Redis 缓存 (对话历史)
    │
    ▼ 调用 LLMProvider (OpenAI/Anthropic等)
    │
    ▼ 通过 UnitOfWork 保存消息到数据库
    │
    ▼ [可选] 缓存结果到 Redis
    │
    ▼ SSE 流式返回
5. Nginx (透传流式响应)
    │
    ▼ 前端接收流式数据并渲染
```

---

## 四、架构设计

### 4.1 后端架构（FastAPI）

#### 4.1.1 目录结构

```
backend/
├── app/
│   ├── api/               # API 路由层
│   │   ├── v1/            # 版本化 API
│   │   │   ├── routes.py  # 资源路由 (角色/教材/对话)
│   │   │   ├── chat.py    # 聊天接口 (流式)
│   │   │   ├── upload.py  # 上传接口
│   │   │   └── auth.py    # 认证接口 (预留)
│   │   └── __init__.py
│   ├── services/          # 业务逻辑层
│   │   ├── llm_providers.py      # LLM提供商
│   │   ├── teaching_service.py   # 教学逻辑
│   │   ├── crud_services.py      # CRUD服务
│   │   ├── upload_service.py     # 上传服务
│   │   └── auth_service.py       # 认证服务 (预留)
│   ├── repositories/      # 数据访问层 (Repository模式)
│   │   ├── base.py        # 基础 Repository 类和接口
│   │   ├── character_repository.py
│   │   ├── material_repository.py
│   │   ├── conversation_repository.py
│   │   └── unit_of_work.py # Unit of Work 模式
│   ├── schemas/           # 数据模型层（Pydantic）
│   │   ├── base.py        # 基础模型
│   │   ├── character.py   # 角色模型
│   │   ├── material.py    # 教材模型
│   │   ├── conversation.py # 对话模型
│   │   ├── message.py     # 消息模型
│   │   └── auth.py        # 认证模型 (预留)
│   ├── core/              # 核心配置
│   │   ├── config.py      # 配置管理
│   │   ├── database.py    # 数据库连接工厂
│   │   ├── redis.py       # Redis连接
│   │   ├── limiter.py     # 限流配置
│   │   ├── logging_config.py
│   │   └── security.py    # 安全工具 (预留)
│   └── __init__.py
├── models/                # SQLAlchemy 模型定义 (独立目录)
│   ├── __init__.py
│   ├── base.py            # 基础模型类
│   ├── character.py       # 角色模型
│   ├── material.py        # 教材模型
│   ├── conversation.py    # 对话模型
│   └── message.py         # 消息模型
├── migrations/            # Alembic 迁移脚本
├── shared/                # 共享目录 (挂载到 /shared)
├── main.py                # 应用入口
├── requirements.txt       # 依赖列表
├── .env                   # 环境变量
└── Dockerfile             # 后端 Dockerfile
```

#### 4.1.2 Repository 模式设计

##### 4.1.2.1 Repository 接口抽象

```python
# backend/app/repositories/base.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional

ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')

class IRepository(ABC, Generic[ModelType]):
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        pass

    @abstractmethod
    async def create(self, obj_in: dict) -> ModelType:
        pass

    @abstractmethod
    async def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        pass

    @abstractmethod
    async def delete(self, db_obj: ModelType) -> bool:
        pass
```

##### 4.1.2.2 基础 Repository 实现

```python
# backend/app/repositories/base.py (续)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.base import Base

class BaseRepository(IRepository[ModelType]):
    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        result = await self.session.execute(
            select(self.model).filter(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        return db_obj

    async def delete(self, db_obj: ModelType) -> bool:
        await self.session.delete(db_obj)
        return True

    async def get_by_field(self, field: str, value) -> Optional[ModelType]:
        result = await self.session.execute(
            select(self.model).filter(getattr(self.model, field) == value)
        )
        return result.scalar_one_or_none()

    async def count(self) -> int:
        result = await self.session.execute(select(self.model))
        return len(result.scalars().all())
```

##### 4.1.2.3 Unit of Work 模式

```python
# backend/app/repositories/unit_of_work.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.core.database import get_session_factory
from app.repositories.character_repository import CharacterRepository
from app.repositories.material_repository import MaterialRepository
from app.repositories.conversation_repository import ConversationRepository

class UnitOfWork:
    def __init__(self):
        self.session_factory = get_session_factory()
        self._session: Optional[AsyncSession] = None
        
    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            self._session = self.session_factory()
        return self._session

    @property
    def characters(self) -> CharacterRepository:
        return CharacterRepository(self.session)

    @property
    def materials(self) -> MaterialRepository:
        return MaterialRepository(self.session)

    @property
    def conversations(self) -> ConversationRepository:
        return ConversationRepository(self.session)

    async def commit(self):
        if self._session:
            await self._session.commit()

    async def rollback(self):
        if self._session:
            await self._session.rollback()

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                await self.commit()
            else:
                await self.rollback()
        finally:
            await self.close()
```

##### 4.1.2.4 Service 层使用示例

```python
# backend/app/services/crud_services.py
from app.repositories.unit_of_work import UnitOfWork
from app.schemas.character import CharacterCreate, CharacterUpdate

class CharacterService:
    @staticmethod
    async def get_all():
        async with UnitOfWork() as uow:
            return await uow.characters.get_all()

    @staticmethod
    async def get_by_id(id: int):
        async with UnitOfWork() as uow:
            return await uow.characters.get_by_id(id)

    @staticmethod
    async def create(character: CharacterCreate):
        async with UnitOfWork() as uow:
            db_obj = await uow.characters.create(character.dict())
            return db_obj

    @staticmethod
    async def update(id: int, character: CharacterUpdate):
        async with UnitOfWork() as uow:
            db_obj = await uow.characters.get_by_id(id)
            if not db_obj:
                return None
            return await uow.characters.update(db_obj, character.dict(exclude_unset=True))

    @staticmethod
    async def delete(id: int):
        async with UnitOfWork() as uow:
            db_obj = await uow.characters.get_by_id(id)
            if not db_obj:
                return False
            await uow.characters.delete(db_obj)
            return True
```

#### 4.1.3 数据库层抽象

##### 4.1.3.1 模型定义（独立目录）

```python
# backend/models/base.py
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

```python
# backend/models/character.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from models.base import Base

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    personality = Column(Text, nullable=False)
    background = Column(Text, nullable=True)
    avatar = Column(String(500), nullable=True)
    avatar_type = Column(String(20), default="emoji")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="character")
```

##### 4.1.3.2 数据库连接工厂

```python
# backend/app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from app.core.config import settings
from models.base import Base

def create_engine_from_settings():
    url = settings.DATABASE_URL
    connect_args = {}
    pool_config = {}

    if "sqlite" in url:
        connect_args["check_same_thread"] = False
        # SQLite 不支持标准连接池，使用 NullPool
        pool_config["poolclass"] = NullPool
    else:
        # PostgreSQL 生产级连接池配置
        pool_config["pool_size"] = 20
        pool_config["max_overflow"] = 10
        pool_config["pool_recycle"] = 3600
        pool_config["pool_pre_ping"] = True

    return create_async_engine(
        url,
        connect_args=connect_args,
        **pool_config
    )

engine = create_engine_from_settings()

def get_session_factory() -> async_sessionmaker:
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

#### 4.1.4 API 版本化设计

| API 端点 | 方法 | 描述 | 需要认证 |
|---------|------|------|---------|
| `/api/v1/health` | GET | 健康检查 | 否 |
| `/api/v1/characters` | GET/POST | 角色列表/创建 | 否/预留 |
| `/api/v1/characters/{id}` | GET/PUT/DELETE | 角色CRUD | 否/预留 |
| `/api/v1/materials` | GET/POST | 教材列表/创建 | 否/预留 |
| `/api/v1/materials/{id}` | GET/PUT/DELETE | 教材CRUD | 否/预留 |
| `/api/v1/conversations` | GET/POST | 对话列表/创建 | 预留 |
| `/api/v1/conversations/{id}` | GET/PUT/DELETE | 对话CRUD | 预留 |
| `/api/v1/chat/{id}/stream` | POST | 流式聊天 | 预留 |
| `/api/v1/uploads` | POST | 文件上传 | 预留 |
| `/api/v1/auth/login` | POST | 用户登录 | 否 |
| `/api/v1/auth/refresh` | POST | 刷新Token | 是 |

---

## 五、部署方案

### 5.1 目录结构（部署后）

```
project/
├── backend/              # 后端代码
│   ├── app/
│   ├── models/
│   ├── migrations/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/             # 前端代码
│   ├── src/
│   ├── index.html
│   ├── vite.config.js
│   ├── nginx.conf
│   └── Dockerfile
├── shared/               # 共享目录 (挂载到容器)
│   └── data/
│       └── uploads/      # 上传文件存储
├── .env                  # 全局环境变量
└── docker-compose.yml    # 容器编排
```

### 5.2 完整 docker-compose.yml

```yaml
version: '3.8'

services:
  nginx:
    build: ./frontend
    container_name: cos2edu-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./shared/data:/usr/share/nginx/html/uploads
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
    networks:
      - cos2edu-network
    restart: unless-stopped

  backend:
    build: ./backend
    container_name: cos2edu-backend
    volumes:
      - ./shared/data:/shared/data
    environment:
      - DATABASE_URL=${DATABASE_URL:-sqlite+aiosqlite:///./data/cos2edu.db}
      - REDIS_URL=${REDIS_URL:-redis://redis:6379}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=${DEBUG:-false}
    networks:
      - cos2edu-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: '2G'
        reservations:
          cpus: '0.5'
          memory: '512M'
    profiles:
      - app
      - all

  postgres:
    image: postgres:16-alpine
    container_name: cos2edu-postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=${DB_USER:-cos2edu}
      - POSTGRES_PASSWORD=${DB_PASSWORD:-password}
      - POSTGRES_DB=${DB_NAME:-cos2edu}
    networks:
      - cos2edu-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: '1G'
    profiles:
      - postgres
      - all

  redis:
    image: redis:7-alpine
    container_name: cos2edu-redis
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    networks:
      - cos2edu-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: '512M'
    profiles:
      - redis
      - all

volumes:
  postgres_data:
  redis_data:

networks:
  cos2edu-network:
    driver: bridge
```

> **profiles 使用说明**：
> - `docker-compose --profile app up` - 仅启动前端 + 后端（SQLite本地数据库）
> - `docker-compose --profile redis up` - 启动 Redis（配合内存限流）
> - `docker-compose --profile postgres up` - 启动 PostgreSQL（如需生产级数据库）
> - `docker-compose --profile all up` - 启动所有服务（完整生产环境）

### 5.3 后端 Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /shared/data/uploads

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

> **注意**：FastAPI 基于 Starlette，使用异步 I/O。`uvicorn` 默认使用单进程单线程模式，配合异步代码可以充分利用 CPU。如需多进程，推荐使用 `gunicorn` 作为进程管理器：
> ```bash
> gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
> ```

---

## 六、数据库初始化与迁移

### 6.1 MVP 初期方案（推荐）

MVP 阶段可使用 `init_db()` 直接创建表结构，无需 Alembic：

```python
# backend/app/core/database.py
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

启动时自动调用：
```python
# backend/main.py
@app.on_event("startup")
async def startup():
    await init_db()
```

**适用场景**：
- MVP 开发初期
- 快速原型验证
- SQLite 本地开发

### 6.2 Alembic 迁移（生产推荐）

当系统需要版本化管理数据库结构时，使用 Alembic：

#### 6.2.1 安装配置

```bash
# 安装 Alembic
pip install alembic

# 初始化 Alembic
alembic init migrations
```

#### 6.2.2 配置 alembic.ini

```ini
# alembic.ini
[alembic]
script_location = migrations

[database]
url = %(DATABASE_URL)s
```

#### 6.2.3 配置 env.py

```python
# migrations/env.py
from logging.config import fileConfig
from sqlalchemy import create_engine
from alembic import context
from models.base import Base
from app.core.config import settings

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    url = settings.DATABASE_URL
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    elif "+aiosqlite" in url:
        url = url.replace("+aiosqlite", "")

    connectable = create_engine(url)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

#### 6.2.4 创建迁移脚本

```bash
# 创建初始迁移（从现有模型生成）
alembic revision --autogenerate -m "Initial migration"

# 查看生成的迁移脚本
cat migrations/versions/xxxx_initial_migration.py

# 执行迁移
alembic upgrade head
```

### 6.3 SQLite → PostgreSQL 迁移流程

```
1. 备份 SQLite 数据
   └── sqlite3 data/cos2edu.db .dump > backup.sql

2. 创建 PostgreSQL 数据库
   └── createdb -h localhost -U cos2edu cos2edu

3. 更新环境变量
   └── DATABASE_URL=postgresql+asyncpg://cos2edu:password@postgres:5432/cos2edu

4. 初始化 Alembic（如果未初始化）
   └── alembic init migrations

5. 创建初始迁移（空表）
   └── alembic revision --autogenerate -m "Initial"

6. 执行迁移（创建表结构）
   └── alembic upgrade head

7. 导入数据（使用 SQLAlchemy 2.0 风格脚本）
   └── python scripts/migrate_data.py

8. 验证数据
   └── psql -h localhost -U cos2edu cos2edu -c "SELECT COUNT(*) FROM characters;"
```

### 6.4 数据导入脚本（SQLAlchemy 2.0 风格）

```python
# scripts/migrate_data.py
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

async def migrate_data():
    # 源数据库（SQLite）
    src_engine = create_engine("sqlite:///./data/cos2edu.db")

    # 目标数据库（PostgreSQL）
    dst_engine = create_async_engine(
        "postgresql+asyncpg://cos2edu:password@localhost:5432/cos2edu"
    )

    # 获取表列表
    with src_engine.connect() as src_conn:
        result = src_conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result]

    # 迁移每个表
    async with dst_engine.begin() as dst_conn:
        for table in tables:
            print(f"Migrating table: {table}")

            # 获取源数据
            with src_engine.connect() as src_conn:
                src_result = src_conn.execute(text(f"SELECT * FROM {table}"))
                columns = src_result.keys()
                rows = src_result.fetchall()

            # 插入目标数据库（SQLAlchemy 2.0 写法）
            for row in rows:
                placeholders = ", ".join([f":{col}" for col in columns])
                query = text(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})")
                await dst_conn.execute(query, dict(zip(columns, row)))

    print("Migration completed!")

if __name__ == "__main__":
    asyncio.run(migrate_data())
```

---

## 七、Mock API 方案（前端独立开发）

### 7.1 技术选型：MSW（Mock Service Worker）

**选型理由**：
- 拦截真实网络请求，无需修改前端代码
- 支持 REST 和 GraphQL
- 可用于浏览器和 Node.js
- 支持 TypeScript

### 7.2 Mock 配置

```javascript
// frontend/src/mocks/handlers.js
import { rest } from 'msw';

export const handlers = [
  rest.get('/api/v1/characters', (req, res, ctx) => {
    return res(ctx.json([
      { id: 1, name: '苏格拉底', avatar: '👨‍🏫' }
    ]));
  }),
  rest.get('/api/v1/conversations', (req, res, ctx) => {
    return res(ctx.json([
      { id: 1, title: '学习对话', character_id: 1 }
    ]));
  }),
  rest.post('/api/v1/chat/:id/stream', (req, res, ctx) => {
    return res(ctx.json({ content: '好问题！让我们一起思考...' }));
  })
];
```

---

## 八、测试策略

### 8.1 测试分层

| 层级 | 工具 | 覆盖范围 |
|-----|------|---------|
| 单元测试 | pytest / Vitest | 单个函数/组件 |
| 集成测试 | pytest + httpx | API 端点 |
| E2E 测试 | Playwright | 端到端流程 |

### 8.2 Repository Mock 测试示例

```python
# tests/unit/test_character_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.crud_services import CharacterService
from app.schemas.character import CharacterCreate

class MockCharacterRepository:
    def __init__(self):
        self.get_all = AsyncMock(return_value=[])
        self.get_by_id = AsyncMock(return_value=None)
        self.create = AsyncMock(return_value=MagicMock(id=1))
        self.update = AsyncMock(return_value=MagicMock(id=1))
        self.delete = AsyncMock(return_value=True)

@pytest.mark.asyncio
async def test_create_character():
    character_data = CharacterCreate(name="Test", personality="friendly")
    result = await CharacterService.create(character_data)
    assert result.id == 1
```

---

## 九、注意事项

1. **数据库切换**：只需修改 `DATABASE_URL` 环境变量即可切换 SQLite/PostgreSQL
2. **Repository 接口**：使用 `IRepository` 接口便于 Mock 和测试
3. **Unit of Work**：确保事务一致性，所有操作在一个会话中完成
4. **SQLAlchemy 2.0**：使用 `text()` 配合参数绑定，避免 SQL 注入
5. **异步部署**：推荐单进程模式，如需多进程使用 gunicorn
6. **Redis 可选**：通过 `profiles` 控制，MVP 初期可使用内存限流（`slowapi` 的内存存储）
7. **连接池**：
   - SQLite：使用 `NullPool`（无连接池）
   - PostgreSQL：默认 `pool_size=20, max_overflow=10`
8. **MVP 开发**：推荐直接使用 `init_db()` 创建表结构，无需配置 Alembic

---

## 十、扩展预留

- [ ] JWT 令牌认证 + 刷新令牌机制
- [ ] Redis 缓存优化 + 数据库读写分离
- [ ] 多用户支持 + 学习进度追踪
- [ ] HTTPS 配置 + 负载均衡 + CI/CD