<div align="center">

# Cos²Edu  ❧

**以问为教**

> 试问：何为生命的第一因？

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Vue](https://img.shields.io/badge/Vue_3-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](./LICENSE)

[何以开始](#-何以开始) · [此为何物](#-此为何物) · [其构若何](#-其构若何) · [更问何处](#-更问何处)

</div>

---

## 何以言之

> 汝来此，欲求答案乎？
>
> 然——予岂敢以答案奉君。予之所赠，唯问而已。

世间 AI 教育之器，莫不急于呈其结论。君问之，彼答之；君惑焉，彼释焉。看似便捷，实则夺君思之权也。

Cos²Edu 不然。此间 AI 导师，不告君以何是，而问君以何故。不问则已，一问再问，直至君自抵其理。

此非一聊天机器人之附教育标签也。此中有叙事引擎为枢，情感引擎令角色生息，知识图谱锚其学径，上下文之预算使每问每答俱有师心。

---

## 此为何物

### ❧ 问学之引

循知识图谱之 DAG 依赖，量上下文之预算，施差异之教。AI 导师察君所学深浅，择其宜者而进——以问为舟，不问则止。

### ❧ 角色之化

角色非一纸人格描述也。情感引擎实时追其 mood 与 trust，因君应而起伏；每角有独属之敏感曲线、表达之风。支持角色卡出入（相容 SillyTavern V2 格式）。

### ❧ 叙事之纬

世界状态引擎掌场景时轴，事件引擎于特定机缘发随机、定时、条件之事。学不复为一直线——课堂讲授、厅堂辩驳、室中考核、隅间闲谈，起承转合，自成篇章。

### ❧ 双轨之库

- **内置精课**：YAML 所撰之结构化课程，预布知识依赖、教学提示、评估之准
- **自载教材**：PDF/DOCX/TXT → 机解其文 → LLM 出纲 → 君予裁夺 → 授之为课

### ❧ WebSocket 实时之通

对谈、情感、景迁、事起——皆由 WebSocket 实时推至。断则复连，状态全量同之。

### ❧ RAG 助忆

FAISS 向量之索引，分块而检，取教材之精义，注于教问之 prompt，非徒全文截断也。

### ❧ 多模之选

OpenAPI · Anthropic · 通义千问 · 智谱 · 豆包 · 文心 · 凡 OpenAI 兼容之 API，一键切换。

### ❧ 课程之图

Mermaid.js 所绘之知识依赖图，学径与进度一目了然。

---

## 其构若何

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (Vue 3)                      │
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

### 七引擎

| 引擎 | 其职 |
|------|------|
| **NarrativeEngine** | 总调度：协诸引擎，共成其事 |
| **TeachingEngine** | 择知识点、筑 Context Budget、施差异之教 |
| **EmotionEngine** | mood/trust 实时追踪（含衰减），角色敏感度曲线，表出之词 |
| **EventEngine** | 时间/条件/随机之事，优先评其轻重 |
| **WorldStateEngine** | 场景管、时轴推、YAML 配载 |
| **CharacterEngine** | 角色登册、配载查询、人格之述 |
| **AssessmentEngine** | 学之评估、知识点掌握之判 |

---

## 何以开始

### 所须

- Python 3.10+
- Node.js 18+

### 源码起之

```bash
git clone https://github.com/littleyellowbicycle/cos2edu.git
cd cos2edu

# 启后端
cd backend
pip install -r requirements.txt
python main.py

# 启前端（另开一窗）
cd frontend
npm install
npm run dev
```

启而后访 **http://localhost:5173**。

### Docker 布之

```bash
docker-compose up -d
```

### 配模型

初用，请至 **设置** 页添 LLM API 密钥：

| 供者 | 模型例 | 何为 |
|------|--------|------|
| OpenAI | gpt-4o, gpt-4o-mini | API Key |
| Anthropic | claude-3-5-sonnet | API Key |
| 阿里通义千问 | qwen-plus, qwen-max | DashScope Key |
| 智谱 AI | glm-4, glm-3-turbo | API Key |
| 豆包 | doubao-pro | API Key + Base URL |
| 文心一言 | ernie-4.0 | API Key + Base URL |
| OpenAI 兼容 | 任意 | 自定义 base_url + model |

---

## 问学之流

```
配模型 → 择角色 → 载教材(不必) → 始苏格拉底之问
                                     ↓
                          知识图谱自规其径
                          情感引擎应声而动
                          事件引擎发叙事之机
                          RAG 精准缀其上下文
```

### 三师

| 角色 | 教风 | 其性 |
|------|------|------|
| **甘雨** | 叙事为引 | 温而善喻，以故事为筏，直觉为桥，俯瞰全局 |
| **刻晴** | 逻辑推导 | 严而有序，从定义起步，步步为营，重数学之精 |
| **三月七** | 实践驱动 | 活而好奇，以代码实验入题，鼓励手触真知 |

### 四境

| 场景 | 其氛 | 可行之事 |
|------|------|---------|
| 教室 | 明净，数据流天际 | 问、答、论、习 |
| 辩论厅 | 圆庭，全息投影 | 辩、陈、问 |
| 考核室 | 寂然，倒计时跃 | 考、省 |
| 休息区 | 怡然，壁浮知识点 | 问、论、省 |

---

## 林中之木

```
cos2edu/
├── backend/
│   ├── app/
│   │   ├── engines/          # 七引擎（核心）
│   │   ├── graph/            # 知识图谱（DAG）
│   │   ├── llm/              # LLM 抽象层 + Context Budget
│   │   ├── parsers/          # 文档解者（PDF/DOCX/TXT）
│   │   ├── rag/              # RAG 检索（FAISS）
│   │   ├── repositories/     # 数据取层（Repository 范式）
│   │   ├── schemas/          # Pydantic 形
│   │   ├── services/         # 服层（Chat/RAG/角色卡）
│   │   ├── state/            # 状管（Critical/Soft 分级）
│   │   ├── tasks/            # 异步任（教材处理）
│   │   ├── api/v1/           # REST + WebSocket API
│   │   └── content/          # YAML 内容（课程/角色/世界观）
│   ├── models/               # SQLAlchemy ORM 形
│   └── main.py
├── frontend/
│   └── src/
│       ├── views/            # 页面
│       ├── components/       # 通用组件
│       ├── stores/           # Pinia 状管
│       ├── composables/      # 组合函数（WebSocket）
│       ├── api/              # HTTP 客
│       └── router/           # 径由
├── docs/                     # 文
└── docker-compose.yml
```

---

## 更问何处

| 文卷 | 所言 |
|------|------|
| [架构](./docs/redesign_plan.md) | 架构全貌与精进之议 |
| [设计](./docs/design.md) | 核心之意与教学之哲 |
| [架构分离](./ARCHITECTURE_SEPARATION.md) | 前后端架构详析 |
| [SillyTavern 对勘](./docs/SillyTavern对比分析与优化方案.md) | 角色/世界书/TTS/Live2D 对勘 |
| [Generative UI 方案](./docs/Cos2Edu%20前端重构与生成式%20UI%20(Generative%20UI)%20方案说明书%20v2.md) | 前端重构与生成式 UI |
| [RAGFlow 之合](./docs/RAGFlow集成方案.md) | RAG 知库集成 |
| [文件上传与 RAG](./docs/文件上传与RAG方案.md) | 文件处理之术 |
| [RAG 部署方策](./docs/RAG部署方案分析.md) | 部署方案对勘 |
| [Windows 打包](./docs/Windows打包方案.md) | 桌面应用打包之术 |

---

## 前程

- [x] Phase 1.0 — 核心之环：TeachingEngine + WorldStateEngine + KnowledgeGraph + WebSocket
- [x] Phase 1.5 — 情感与事：EmotionEngine + EventEngine + Parsers + RAG + Material Pipeline
- [x] Phase 1.8 — 角色卡出入 + 课程脑图 + 大纲分类管
- [ ] Phase 2.0 — AssessmentEngine + 场景切换 UI + 课程编辑器
- [ ] Phase 2.5 — TTS 语合（EdgeTTS）+ Live2D 角色呈
- [ ] Phase 3.0 — 多生协学 + 学习分析仪表盘
- [ ] Phase 4.0 — 插件系统 + 自定义世界观编辑器

---

## 致谢

此间之思，师于二文：

- [《怎样用AI让自己沉迷学习？》](https://zhuanlan.zhihu.com/p/2012398047620014256)
- [《AI沉迷学习指南》](https://zhuanlan.zhihu.com/p/2016557736364634882)

谢 **@硅与之** 与 **@null** 二君之述。

---

## 许

[MIT License](./LICENSE)

<div align="center">

**子若以此器为益，愿赐一星 ⭐ 否？**

❧

</div>
