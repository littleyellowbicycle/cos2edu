<div align="center">

# ❧ 苏格拉底 AI 教学系统

**让 AI 导师通过提问引导你自主思考——不是灌输知识，而是唤醒思考力**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Vue](https://img.shields.io/badge/Vue-3-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](./LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat-square)](../../pulls)

[🚀 快速开始](#-快速开始) · [✨ 特性](#-核心特性) · [🏗 架构](#-架构) · [📖 文档](#-文档) · [🤝 贡献](#-贡献)

</div>

---

## 理念

> 教育不是灌满一桶水，而是点燃一把火。 ——叶芝

传统 AI 教育工具直接给答案，学生记住结论却不知所以然。苏格拉底 AI 教学系统反其道而行——**AI 不会告诉你答案，而是通过连续追问引导你自己推理出结论**。

这不是聊天机器人加上教育标签。这是一套**叙事驱动的教学架构**：世界观引擎推进剧情，情感引擎让角色"活"起来，知识图谱确保学习路径有序，上下文预算让每条 prompt 都有教学目的。

---

## ✨ 核心特性

### 🧠 苏格拉底式教学引擎
不是普通聊天——基于知识图谱的 DAG 依赖检测、上下文预算分配、差异化教学提示，每一步引导都经过精心编排。

### 🎭 动态角色系统
角色不只是人格描述字符串。情感引擎实时追踪 mood/trust，基于学生反馈动态变化；每个角色拥有独立的敏感度曲线和表达风格。

### 🌍 叙事驱动架构
世界状态引擎管理场景与时间线，事件引擎在特定条件下触发随机/定时/条件事件——学习不再是一条直线，而是一场有起承转合的旅程。

### 📚 双轨内容系统
- **内置精品课程**：YAML 编写的结构化课程，预定义知识依赖、教学提示、评估标准
- **用户上传教材**：PDF/DOCX/TXT → 自动解析 → LLM 生成大纲 → 人工确认 → 结构化教学

### 🔌 WebSocket 实时通信
对话流、情感更新、场景切换、事件触发——全部通过 WebSocket 实时推送，支持断连自动重连 + 状态全量同步。

### 🔍 RAG 增强检索
FAISS 向量索引 + 分块检索，将教材内容精准注入教学 prompt，而非简单的全文截断。

### 🎯 多模型支持
OpenAI · Anthropic · 阿里通义千问 · 智谱 AI · 任何 OpenAI 兼容 API，一键切换。

---

## 🏗 架构

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                  │
│  Chat · Curriculum · Characters · Timeline · Settings │
│          │ Pinia Narrative Store │ WebSocket Composable           │
└─────────────────────┬───────────────────────────────┘
                      │ WebSocket + REST
┌─────────────────────┴───────────────────────────────┐
│                 FastAPI Backend                       │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │            Narrative Engine (总调度)              │ │
│  │  Teaching · Emotion · Event · World · Character  │ │
│  └─────────────────┬───────────────────────────────┘ │
│                    │                                  │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────────┐ │
│  │Knowledge│  │Context │  │ RAG    │  │  State     │ │
│  │ Graph  │  │Budget  │  │Service │  │  Manager   │ │
│  │(DAG)   │  │(Token) │  │(FAISS) │  │(Critical+  │ │
│  └────────┘  └────────┘  └────────┘  │ Soft Tier) │ │
│                                       └────────────┘ │
│  ┌──────────────────────────────────────────────────┐│
│  │  YAML Content    │    Material Pipeline           ││
│  │  ─ Syllabus      │    Parse → Index → Outline     ││
│  │  ─ Modules       │    → Pending Review → Ready    ││
│  │  ─ Characters     │                               ││
│  │  ─ World Settings │                               ││
│  └──────────────────────────────────────────────────┘│
│                                                       │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ SQLAlchemy │  │   LLM Provider│  │  Parsers     │ │
│  │  (SQLite)  │  │  (Multi-API)  │  │  PDF/DOCX/TXT│ │
│  └────────────┘  └──────────────┘  └──────────────┘ │
└───────────────────────────────────────────────────────┘
```

### 领域引擎

| 引擎 | 职责 |
|------|------|
| **NarrativeEngine** | 总调度：编排 Teaching/Emotion/Event/World 四引擎协同 |
| **TeachingEngine** | 知识点选取 + Context Budget 构建 + 差异化教学提示 |
| **EmotionEngine** | mood/trust 追踪（含衰减）、角色敏感度曲线、表达生成 |
| **EventEngine** | 时间事件 / 条件事件 / 随机事件触发，优先级评估 |
| **WorldStateEngine** | 场景管理 + 时间推进 + YAML 配置加载 |
| **CharacterEngine** | 角色注册、配置加载、人格描述查询 |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- SQLite (内置)

### 源码运行

```bash
# 1. 克隆项目
git clone https://github.com/littleyellowbicycle/cos2edu.git
cd cos2edu

# 2. 启动后端
cd backend
pip install -r requirements.txt
python main.py

# 3. 启动前端（新终端）
cd frontend
npm install
npm run dev
```

访问 **http://localhost:5173** 开始使用。

### Docker 部署

```bash
docker-compose up -d
```

### 配置模型

首次使用请前往 **设置** 页面添加 LLM API 密钥，支持：

| 提供商 | 模型示例 |
|--------|----------|
| OpenAI | gpt-4o, gpt-3.5-turbo |
| Anthropic | claude-3-5-sonnet |
| 阿里通义千问 | qwen-plus, qwen-max |
| 智谱 AI | glm-4, glm-3-turbo |
| 任何 OpenAI 兼容 API | 自定义 base_url + model |

---

## 📖 使用流程

```
配置模型 → 选择角色 → 上传教材(可选) → 开始苏格拉底式对话
                                        ↓
                              知识图谱自动规划路径
                              情感引擎动态响应
                              事件引擎触发叙事
                              RAG 精准注入上下文
```

---

## 📂 项目结构

```
cos2edu/
├── backend/
│   ├── app/
│   │   ├── engines/          # 领域引擎 (核心业务)
│   │   ├── graph/            # 知识图谱 (DAG)
│   │   ├── llm/              # LLM 抽象 + Context Budget
│   │   ├── parsers/          # 文档解析器 (PDF/DOCX/TXT)
│   │   ├── state/            # 状态管理 (Critical/Soft 分级)
│   │   ├── tasks/            # 异步任务 (教材处理管线)
│   │   ├── services/         # 服务层 (Chat/RAG)
│   │   ├── api/v1/           # REST + WebSocket API
│   │   └── content/          # YAML 内容 (课程/角色/世界观)
│   └── main.py
├── frontend/
│   └── src/
│       ├── views/            # 页面组件
│       ├── stores/           # Pinia 状态 (含 Narrative Store)
│       ├── composables/       # 组合式函数 (WebSocket)
│       └── api/              # HTTP 客户端
├── docs/                     # 设计文档
├── packaging/                # 打包脚本
└── docker-compose.yml
```

---

## 📚 文档

| 文档 | 说明 |
|------|------|
| [重新设计方案 v2](./docs/redesign_plan.md) | 完整架构设计，含 6 条优化建议 |
| [设计理念](./docs/design.md) | 核心设计理念与教学哲学 |
| [架构分离文档](./ARCHITECTURE_SEPARATION.md) | 前后端架构详解 |
| [RAGFlow 集成](./docs/RAGFlow集成方案.md) | RAG 知识库集成方案 |
| [文件上传与 RAG](./docs/文件上传与RAG方案.md) | 文件处理技术方案 |

---

## 🧭 路线图

- [x] Phase 1.0 — 核心循环：TeachingEngine + WorldStateEngine + KnowledgeGraph + WebSocket
- [x] Phase 1.5 — 情感与事件：EmotionEngine + EventEngine + Parsers + RAG + Material Pipeline
- [ ] Phase 2.0 — AssessmentEngine + 场景切换 UI + 课程编辑器
- [ ] Phase 3.0 — 多学生协作 + 学习分析仪表盘
- [ ] Phase 4.0 — Plugin 系统 + 自定义世界观编辑器

---

## 🙏 致谢

本项目的设计和实现受到了以下文章的启发：

- [《怎样用AI让自己沉迷学习？》](https://zhuanlan.zhihu.com/p/2012398047620014256) — 探索 AI 教育应用的灵感来源
- [《AI沉迷学习指南》](https://zhuanlan.zhihu.com/p/2016557736364634882) — 苏格拉底式 AI 教学法的实践参考

感谢 **@硅与之** 和 **@null** 两位作者的分享！

---

## 📜 License

[MIT License](./LICENSE)

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star！**

</div>