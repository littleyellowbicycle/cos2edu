<div align="center">

# Cos²Edu 架构

</div>

---

## 🏗 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                      │
│  Chat · Curriculum · Characters · Conversations · Settings│
│         Pinia Store │ WebSocket Composable │ API Client   │
└──────────────────────────┬──────────────────────────────┘
                           │ WebSocket + REST
┌──────────────────────────┴──────────────────────────────┐
│                   FastAPI Backend                         │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Narrative Engine (总调度)                │ │
│  │  Teaching · Emotion · Event · World · Character      │ │
│  │  Assessment                                          │ │
│  └────────────────────┬────────────────────────────────┘ │
│                       │                                   │
│  ┌──────────┐  ┌──────────┐  ┌────────┐  ┌────────────┐ │
│  │Knowledge │  │ Context  │  │  RAG   │  │   State    │ │
│  │  Graph   │  │  Budget  │  │Service │  │  Manager   │ │
│  │  (DAG)   │  │ (Token)  │  │(FAISS) │  │(Critical + │ │
│  └──────────┘  └──────────┘  └────────┘  │ Soft Tier) │ │
│                                           └────────────┘ │
│  ┌──────────────────────────────────────────────────────┐│
│  │  YAML Content       │    Material Pipeline            ││
│  │  ─ Syllabus         │    Parse → Index → Outline      ││
│  │  ─ Modules          │    → Pending Review → Ready     ││
│  │  ─ Characters       │                                 ││
│  │  ─ World Settings   │                                 ││
│  └──────────────────────────────────────────────────────┘│
│                                                           │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ SQLAlchemy │  │ LLM Provider  │  │     Parsers      │ │
│  │  (SQLite)  │  │ (Multi-API)   │  │ PDF/DOCX/TXT     │ │
│  └────────────┘  └──────────────┘  └──────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

---

## 领域引擎

| 引擎 | 职责 |
|------|------|
| **NarrativeEngine** | 总调度：编排所有引擎协同工作 |
| **TeachingEngine** | 知识点选取 + Context Budget 构建 + 差异化教学提示 |
| **EmotionEngine** | mood/trust 实时追踪（含衰减）、角色敏感度曲线、表达生成 |
| **EventEngine** | 时间事件 / 条件事件 / 随机事件触发，优先级评估 |
| **WorldStateEngine** | 场景管理 + 时间推进 + YAML 配置加载 |
| **CharacterEngine** | 角色注册、配置加载、人格描述查询 |
| **AssessmentEngine** | 学习评估、知识点掌握度判定 |

---

## 项目结构

```
cos2edu/
├── backend/
│   ├── app/
│   │   ├── engines/          # 领域引擎（核心业务逻辑）
│   │   ├── graph/            # 知识图谱（DAG 依赖）
│   │   ├── llm/              # LLM 抽象层 + Context Budget
│   │   ├── parsers/          # 文档解析器（PDF/DOCX/TXT）
│   │   ├── rag/              # RAG 检索服务（FAISS）
│   │   ├── repositories/     # 数据访问层（Repository 模式）
│   │   ├── schemas/          # Pydantic 数据模型
│   │   ├── services/         # 服务层（Chat/RAG/角色卡）
│   │   ├── state/            # 状态管理（Critical/Soft 分级）
│   │   ├── tasks/            # 异步任务（教材处理管线）
│   │   ├── api/v1/           # REST + WebSocket API
│   │   └── content/          # YAML 内容（课程/角色/世界观）
│   ├── models/               # SQLAlchemy ORM 模型
│   └── main.py
├── frontend/
│   └── src/
│       ├── views/            # 页面组件
│       ├── components/       # 通用组件
│       ├── stores/           # Pinia 状态管理
│       ├── composables/      # 组合式函数（WebSocket）
│       ├── api/              # HTTP 客户端
│       └── router/           # 路由配置
├── docs/                     # 设计文档
└── docker-compose.yml
```
