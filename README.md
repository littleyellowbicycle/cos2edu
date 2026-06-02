<div align="center">

# Cos2Edu  ❧

**叙事驱动的苏格拉底式 AI 教学系统**

不是灌输知识，而是通过追问唤醒思考力

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Vue](https://img.shields.io/badge/Vue_3-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](./LICENSE)

[快速开始](#-快速开始) · [核心特性](#-核心特性) · [架构](#-架构) · [文档](#-文档)

</div>

---

## 理念

> 教育不是灌满一桶水，而是点燃一把火。 ——叶芝

传统 AI 教育工具直接给答案，学生记住结论却不知所以然。Cos2Edu 反其道而行——**AI 导师不会告诉你答案，而是通过连续追问引导你自己推理出结论**。

这不是聊天机器人加上教育标签。这是一套叙事驱动的教学架构：世界观引擎推进剧情，情感引擎让角色"活"起来，知识图谱确保学习路径有序，上下文预算让每条 prompt 都有教学目的。

---

## ✨ 核心特性

### 🧠 苏格拉底式教学引擎

基于知识图谱 DAG 依赖检测、上下文预算分配、差异化教学提示，每一步引导都经过精心编排。AI 导师根据学生当前掌握程度选择下一个知识点，用提问而非陈述推进学习。

### 🎭 动态角色系统

角色不只是人格描述字符串。情感引擎实时追踪 mood/trust，基于学生反馈动态变化；每个角色拥有独立的敏感度曲线和表达风格。支持角色卡导入导出（兼容 SillyTavern V2 格式）。

### 🌍 叙事驱动架构

世界状态引擎管理场景与时间线，事件引擎在特定条件下触发随机/定时/条件事件。学习不再是一条直线，而是一场有起承转合的旅程——教室上课、辩论厅交锋、考核室检验、休息区闲聊。

### 📚 双轨内容系统

- **内置精品课程**：YAML 编写的结构化课程，预定义知识依赖、教学提示、评估标准
- **用户上传教材**：PDF/DOCX/TXT → 自动解析 → LLM 生成大纲 → 人工确认 → 结构化教学

### 🔌 WebSocket 实时通信

对话流、情感更新、场景切换、事件触发——全部通过 WebSocket 实时推送，支持断连自动重连 + 状态全量同步。

### 🔍 RAG 增强检索

FAISS 向量索引 + 分块检索，将教材内容精准注入教学 prompt，而非简单的全文截断。

### 🎯 多模型支持

OpenAI · Anthropic · 阿里通义千问 · 智谱 AI · 豆包 · 文心一言 · 任何 OpenAI 兼容 API，一键切换。

### 🗺️ 课程脑图

Mermaid.js 渲染的知识点依赖关系图，直观展示学习路径和当前进度。

---

## 🏗 架构

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

### 领域引擎

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

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 源码运行

```bash
# 克隆项目
git clone https://github.com/littleyellowbicycle/cos2edu.git
cd cos2edu

# 启动后端
cd backend
pip install -r requirements.txt
python main.py

# 启动前端（新终端）
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

首次使用请前往 **设置** 页面添加 LLM API 密钥：

| 提供商 | 模型示例 | 配置方式 |
|--------|----------|----------|
| OpenAI | gpt-4o, gpt-4o-mini | API Key |
| Anthropic | claude-3-5-sonnet | API Key |
| 阿里通义千问 | qwen-plus, qwen-max | DashScope Key |
| 智谱 AI | glm-4, glm-3-turbo | API Key |
| 豆包 | doubao-pro | API Key + Base URL |
| 文心一言 | ernie-4.0 | API Key + Base URL |
| OpenAI 兼容 | 任意模型 | 自定义 base_url + model |

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

### 内置角色

项目内置三个风格迥异的 AI 导师，每个角色拥有独立的教学风格和情感模型：

| 角色 | 教学风格 | 特点 |
|------|----------|------|
| **甘雨** | 叙事引导 | 温柔耐心，用故事和比喻建立直觉，从宏观视角切入 |
| **刻晴** | 逻辑推导 | 严谨高效，从定义出发逐步推导，强调数学精确性 |
| **三月七** | 实践驱动 | 活泼好奇，用代码和实验引入概念，鼓励动手尝试 |

### 世界观场景

| 场景 | 氛围 | 允许的行为 |
|------|------|-----------|
| 教室 | 明亮，数据流天际线 | 教学、提问、讨论、练习 |
| 辩论厅 | 圆形辩论场，全息投影 | 辩论、陈述、提问 |
| 考核室 | 安静，倒计时跳动 | 考试、回顾 |
| 休息区 | 舒适，壁画浮现知识点 | 提问、讨论、回顾 |

---

## 📂 项目结构

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

---

## 📚 文档

| 文档 | 说明 |
|------|------|
| [架构设计](./docs/redesign_plan.md) | 完整架构设计，含优化建议 |
| [设计理念](./docs/design.md) | 核心设计理念与教学哲学 |
| [架构分离文档](./ARCHITECTURE_SEPARATION.md) | 前后端架构详解 |
| [SillyTavern 对比分析](./docs/SillyTavern对比分析与优化方案.md) | 角色系统/世界书/TTS/Live2D 对比与优化方案 |
| [Generative UI 方案](./docs/Cos2Edu%20前端重构与生成式%20UI%20(Generative%20UI)%20方案说明书%20v2.md) | 前端重构与生成式 UI 架构 |
| [RAGFlow 集成](./docs/RAGFlow集成方案.md) | RAG 知识库集成方案 |
| [文件上传与 RAG](./docs/文件上传与RAG方案.md) | 文件处理技术方案 |
| [RAG 部署方案](./docs/RAG部署方案分析.md) | RAG 部署方案对比分析 |
| [Windows 打包](./docs/Windows打包方案.md) | Windows 桌面应用打包方案 |

---

## 🧭 路线图

- [x] Phase 1.0 — 核心循环：TeachingEngine + WorldStateEngine + KnowledgeGraph + WebSocket
- [x] Phase 1.5 — 情感与事件：EmotionEngine + EventEngine + Parsers + RAG + Material Pipeline
- [x] Phase 1.8 — 角色卡导入导出 + 课程脑图 + 大纲分类管理
- [ ] Phase 2.0 — AssessmentEngine + 场景切换 UI + 课程编辑器
- [ ] Phase 2.5 — TTS 语音合成（EdgeTTS）+ Live2D 角色渲染
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
