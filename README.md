# 苏格拉底AI教学系统

基于苏格拉底教学法的AI教学系统，让AI导师通过提问引导你自主思考。

## 功能特点

- 🧠 **苏格拉底教学法**：不直接给出答案，通过问题引导自主思考
- 🎭 **个性化角色**：选择不同性格的AI导师（三月七、刻晴、苏格拉底等）
- 📚 **自定义教材**：上传任意教材内容，AI基于教材进行教学
- 🔧 **多模型支持**：支持OpenAI、Anthropic、阿里通义千问、智谱AI等多种LLM
- 💻 **本地部署**：完全本地运行，数据安全私密

## 快速开始

### 1. 安装依赖（MVP 最小依赖）

```bash
pip install -r requirements-prod.txt
```

**可选依赖**：
- Redis（用于限流和并发控制）：`pip install -r requirements-redis.txt`
- Alembic（数据库迁移，PG 迁移时需要）：`pip install alembic`

### 2. 初始化数据

```bash
python init_data.py
```

这会创建默认角色和示例教材。

### 3. 配置模型

启动服务后，访问 `http://localhost:8000/settings` 配置你的LLM API密钥。

### 4. 启动服务

```bash
python main.py
```

然后访问 http://localhost:8000

## 使用流程

1. **配置模型**：在设置页面添加你的LLM API密钥
2. **添加教材**：在教材管理页面添加你想要学习的内容
3. **选择角色**：选择一个你喜欢的AI导师角色
4. **开始学习**：创建新对话，与AI导师进行苏格拉底式对话

## 项目结构

```
cos2edu/
├── app/
│   ├── api/              # API路由
│   │   ├── routes.py     # 基础CRUD路由
│   │   ├── chat.py       # 聊天接口
│   │   └── pages.py      # 页面路由
│   ├── core/             # 核心配置
│   │   ├── config.py     # 配置管理
│   │   └── database.py   # 数据库连接工厂
│   ├── schemas/          # Pydantic模型
│   └── services/         # 业务逻辑
│       ├── llm_providers.py   # LLM提供商
│       ├── crud_services.py   # CRUD服务
│       └── teaching_service.py # 教学逻辑
├── static/               # 前端静态文件
└── data/                 # 数据目录
```

## 支持的模型提供商

| 提供商 | 环境变量 | 常见模型 |
|--------|----------|----------|
| OpenAI | OPENAI_API_KEY | gpt-4o, gpt-3.5-turbo |
| Anthropic | ANTHROPIC_API_KEY | claude-3-5-sonnet-20241022 |
| 阿里通义千问 | DASHSCOPE_API_KEY | qwen-plus, qwen-max |
| 智谱AI | ZHIPU_API_KEY | glm-4, glm-3-turbo |

## 苏格拉底教学法

苏格拉底教学法的核心是**提问而非灌输**：

1. **不直接给出答案**：让学生自己推理
2. **循序渐进的问题**：从已知到未知
3. **关注推理过程**：答案不重要，思考过程才重要
4. **鼓励质疑精神**：培养批判性思维

---

## 前后端分离架构方案（MVP）

### 目标架构

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
│   (Nginx)         │      │   (FastAPI)       │      │ PostgreSQL/SQLite │
└───────────────────┘      └───────────────────┘      ├───────────────────┤
                                                      │ Redis             │
                                                      └───────────────────┘
```

### Repository 模式（数据层抽象）

**接口抽象**：
```python
class IRepository(ABC, Generic[ModelType]):
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        pass
    @abstractmethod
    async def create(self, obj_in: dict) -> ModelType:
        pass
```

**Unit of Work 模式**：
```python
class UnitOfWork:
    @property
    def characters(self) -> CharacterRepository:
        return CharacterRepository(self.session)
    
    async def commit(self):
        await self._session.commit()
```

**目录结构**：
```
backend/
├── app/
│   ├── repositories/       # Repository层
│   │   ├── base.py        # 接口和基础实现
│   │   └── unit_of_work.py # Unit of Work
│   ├── services/          # 业务逻辑（依赖Repository）
│   └── core/
│       └── database.py    # 连接工厂
└── models/                 # SQLAlchemy模型（独立目录）
```

### 数据库迁移方案

#### MVP 阶段（SQLite）
- 使用 `create_all` 自动创建表结构
- 运行 `python init_data.py` 初始化默认数据
- 手动迁移脚本 `migrate_db.py` 处理 schema 变更

#### PostgreSQL 迁移阶段
```bash
# 安装 Alembic
pip install alembic

# 创建迁移脚本
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# SQLite → PostgreSQL 迁移步骤：
# 1. 备份 SQLite 数据：sqlite3 data/app.db .dump > backup.sql
# 2. 更新 DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/db
# 3. 执行 Alembic 迁移创建表结构
# 4. 运行数据导入脚本
```

**数据导入脚本（SQLAlchemy 2.0风格）**：
```python
async with dst_engine.begin() as dst_conn:
    for row in rows:
        query = text(f"INSERT INTO table ({cols}) VALUES ({placeholders})")
        await dst_conn.execute(query, dict(zip(columns, row)))
```

### 部署配置

```bash
# 开发环境（单进程）
uvicorn main:app --host 0.0.0.0 --port 8000

# 生产环境（多进程）
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### 数据库切换

只需修改 `DATABASE_URL` 环境变量：
- SQLite：`sqlite+aiosqlite:///./data/cos2edu.db`
- PostgreSQL：`postgresql+asyncpg://user:pass@postgres:5432/db`

### Mock API（前端独立开发）

使用 MSW 实现前端独立开发：
```javascript
import { rest } from 'msw';

export const handlers = [
  rest.get('/api/v1/characters', (req, res, ctx) => {
    return res(ctx.json([{ id: 1, name: '苏格拉底' }]));
  })
];
```

---

## 参考

本项目参考了知乎文章《怎样用AI让自己沉迷学习？》中的教育理念。

## 架构文档

详细的架构设计文档请参考 [ARCHITECTURE_SEPARATION.md](./ARCHITECTURE_SEPARATION.md)