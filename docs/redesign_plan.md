# 苏格拉底AI教学系统 - 重新设计方案

> 基于 `design.md` 理念，对当前项目进行叙事驱动架构重构的完整方案。

---

## 一、核心理念变化

| 维度 | 当前 | 新设计 |
|------|------|--------|
| **教学范式** | 自由对话 + 手动上传教材 | 结构化课程体系驱动，引擎按大纲规划教学路径 |
| **通信方式** | REST + SSE 流式 | **WebSocket 为主** (对话/事件/状态同步)，REST 为辅 (历史查询/配置) |
| **角色系统** | 静态人格描述 | 动态角色：情感引擎 + 关系系统 + 差异化教学提示 |
| **叙事驱动** | 无 | 世界观状态、时间线推进、事件触发、场景切换 |
| **内容来源** | 仅支持用户上传 | 双轨制：内置精品课程 (预编写 YAML) + 用户上传教材 (LLM 自动提取大纲) |
| **数据存储** | SQLite ORM (全关系型) | YAML 文件 (课程内容) + SQLite (运行时状态) 双层存储 |
| **前端状态** | Pinia store (CRUD) | **Narrative State Manager** 维护轻量世界状态镜像 |
| **架构风格** | 分层 CRUD | **领域引擎模式** (WorldState / Character / Event / Emotion / Teaching / Assessment Engines) |

---

## 二、新项目结构

```
cos2edu/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── routes.py            # REST: 历史记录、配置管理、健康检查
│   │   │       ├── ws.py                # WebSocket 主入口
│   │   │       └── auth.py              # 认证 (预留)
│   │   ├── engines/                     # 领域引擎 (核心业务逻辑)
│   │   │   ├── __init__.py
│   │   │   ├── world_state_engine.py    # 世界观状态引擎
│   │   │   ├── character_engine.py      # 角色注册与管理引擎
│   │   │   ├── event_engine.py          # 事件引擎 (时间/条件/随机)
│   │   │   ├── emotion_engine.py        # 情感引擎
│   │   │   ├── teaching_engine.py       # 教学协作引擎 (核心)
│   │   │   ├── assessment_engine.py     # 考核引擎
│   │   │   └── narrative_engine.py      # 叙事编排引擎 (总调度)
│   │   ├── llm/                         # LLM 抽象层 (复用现有多 Provider 逻辑)
│   │   │   ├── __init__.py
│   │   │   ├── provider.py              # LLMProvider (多 Provider 支持)
│   │   │   └── prompt_builder.py        # Prompt 构建器 (课程+角色+场景)
│   │   ├── parsers/                     # 文档解析器 (新增)
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # 解析器抽象基类 + 错误码
│   │   │   ├── pdf_parser.py            # PDF 解析 (pdfplumber/PyMuPDF)
│   │   │   ├── docx_parser.py           # DOCX 解析 (python-docx)
│   │   │   ├── text_parser.py           # TXT/MD 解析 (含编码检测)
│   │   │   └── parser_registry.py       # 解析器注册与格式分发
│   │   ├── rag/                         # RAG 层 (新增)
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # RAG 提供者接口抽象
│   │   │   ├── simple_rag.py            # LlamaIndex + FAISS 最小实现
│   │   │   └── ragflow_client.py        # RAGFlow 客户端 (未来扩展)
│   │   ├── repositories/                # 数据访问层 (保留 UoW 模式)
│   │   │   ├── base.py
│   │   │   ├── unit_of_work.py
│   │   │   ├── character_repository.py
│   │   │   ├── material_repository.py
│   │   │   ├── conversation_repository.py
│   │   │   ├── world_state_repository.py     # 新增
│   │   │   ├── character_state_repository.py  # 新增
│   │   │   ├── learning_progress_repository.py # 新增
│   │   │   └── syllabus_repository.py        # 新增
│   │   ├── schemas/                     # Pydantic 模型
│   │   │   ├── ws_protocol.py           # WebSocket 消息协议定义 (新增)
│   │   │   ├── enums.py                 # 新增 MaterialStatus, 引擎相关枚举
│   │   │   └── ...
│   │   ├── tasks/                       # 异步任务 (新增)
│   │   │   ├── __init__.py
│   │   │   ├── material_pipeline.py     # 教材处理流水线 (解析→索引→大纲)
│   │   │   └── task_registry.py         # 内存任务状态追踪
│   │   └── core/                        # 基础设施 (保留)
│   │       ├── config.py
│   │       ├── database.py
│   │       ├── limiter.py
│   │       └── ...
│   ├── models/                          # SQLAlchemy ORM (新增叙事相关模型)
│   │   ├── base.py
│   │   ├── character.py
│   │   ├── material.py                  # 改造：新增状态机字段
│   │   ├── conversation.py              # 改造：关联知识点+场景
│   │   ├── message.py
│   │   ├── model_config.py
│   │   ├── world_state.py               # 新增
│   │   ├── character_state.py           # 新增
│   │   ├── learning_progress.py         # 新增
│   │   ├── syllabus.py                  # 新增
│   │   ├── knowledge_point.py           # 新增
│   │   └── event_log.py                 # 新增
│   ├── content/                         # 教学内容存储 (新增)
│   │   ├── syllabus.yaml               # 课程大纲 (内置课程)
│   │   ├── modules/                     # 知识模块
│   │   │   ├── 01_ml_basics.yaml
│   │   │   ├── 02_neural_networks.yaml
│   │   │   └── ...
│   │   ├── exercises/                   # 练习题库
│   │   │   ├── week_01.yaml
│   │   │   └── ...
│   │   ├── resources/                   # 参考资源
│   │   │   ├── reading_list.yaml
│   │   │   └── datasets.yaml
│   │   ├── characters/                  # 角色教学配置
│   │   │   ├── ganyu.yaml
│   │   │   ├── keqing.yaml
│   │   │   └── march7th.yaml
│   │   └── world/                       # 世界观设定
│   │       ├── settings.yaml           # 世界参数
│   │       ├── events.yaml             # 事件定义
│   │       └── scenes/                 # 场景脚本
│   │           ├── classroom.yaml
│   │           ├── debate.yaml
│   │           └── exam.yaml
│   └── main.py
│
├── frontend/
│   └── src/
│       ├── views/
│       │   ├── Home.vue               # 仪表盘 (时间线 + 进度)
│       │   ├── Chat.vue               # 对话界面 (WebSocket 流式)
│       │   ├── Timeline.vue           # 90天倒计时可视化 (新增)
│       │   ├── Characters.vue         # 角色状态卡片 (动态情感) (改造)
│       │   ├── Scene.vue              # 场景切换/展示 (新增)
│       │   ├── Exam.vue               # 考核/辩论赛界面 (新增)
│       │   ├── Curriculum.vue         # 课程进度 (新增)
│       │   └── Settings.vue           # 配置 (保留)
│       ├── stores/
│       │   ├── narrative.js           # 叙事状态管理 (新增，核心)
│       │   ├── chat.js                # 聊天状态
│       │   └── settings.js            # 配置状态
│       ├── composables/
│       │   ├── useWebSocket.js        # WebSocket 连接管理 (新增)
│       │   └── useTimeline.js         # 时间线逻辑 (新增)
│       ├── api/
│       │   └── index.js               # REST API (保留, 精简)
│       └── ...
```

---

## 三、双轨制内容体系

### 3.1 场景 A：内置精品课程

由内容设计师预先编写完整 YAML，包含教学策略和题库。

```yaml
# content/syllabus.yaml
course:
  name: "AI 机器学习入门"
  total_days: 90
  phases:
    - name: "基础阶段"
      days: [1, 30]
      modules: [ml_basics, python_ml, math_review]
    - name: "进阶阶段"
      days: [31, 60]
      modules: [neural_networks, deep_learning, cv_basics]
    - name: "实战阶段"
      days: [61, 90]
      modules: [nlp, project_practice]
```

```yaml
# content/modules/02_neural_networks.yaml
id: neural_networks
name: "神经网络基础"
order: 2
estimated_hours: 16
prerequisites: [ml_basics]

knowledge_points:
  - id: perceptron
    name: "感知机"
    difficulty: 2
    estimated_minutes: 45
    key_concepts: ["线性分类", "激活函数", "损失函数"]
    teaching_hints:
      ganyu: "从MP神经元的历史故事讲起，用生活中'是/否'判断的例子建立直觉"
      keqing: "直接给出感知机的数学定义和更新公式，然后推导收敛性证明"
      march7th: "先让学生用Python写一个感知机分类二维点，再回头解释原理"
    suggested_questions:
      - "如果数据不是线性可分的，感知机会发生什么？"
      - "想一想，多个感知机组合起来能解决什么问题？"
    exercises:
      - type: "coding"
        prompt: "使用 NumPy 实现一个感知机，对 AND 逻辑门进行分类"
      - type: "concept"
        prompt: "解释为什么感知机无法解决 XOR 问题"
```

```yaml
# content/characters/ganyu.yaml
id: ganyu
name: "甘雨"
teaching_style: "narrative_guided"
personality: "温柔耐心的叙事型导师"
background: "千年历史的见证者，喜欢用故事和比喻来解释复杂概念"

emotion_profile:
  base_mood: 0.7
  mood_decay: 0.02
  event_sensitivity:
    student_correct: +0.05
    student_wrong: -0.02
    student_engaged: +0.08
    time_pressure: -0.1

relationship_dynamics:
  trust_growth_rate: 0.01
  trust_decay_rate: 0.005
  max_trust: 1.0
```

```yaml
# content/world/settings.yaml
world:
  name: "AI 学院"
  time_scale: 1
  start_scene: "classroom"
  narrative_tone: "轻科幻校园风"

scenes:
  - id: "classroom"
    name: "教室"
    description: "明亮的教室，窗外是数据流构成的城市天际线"
    allowed_actions: [teach, question, discuss]
  - id: "debate_hall"
    name: "辩论厅"
    description: "圆形辩论场，中央全息投影显示着争议主题"
    allowed_actions: [debate, present, vote]
  - id: "exam_room"
    name: "考核室"
    description: "安静的考核室，倒计时在墙上缓缓跳动"
    allowed_actions: [exam, review]
```

### 3.2 场景 B：用户上传教材

用户上传任意教材，系统通过 LLM 自动提取结构化大纲，运行时动态生成教学提示。

```
用户上传教材 (PDF/DOCX/TXT/MD)
    │
    ▼
┌──────────────────────────────────────────┐
│  Step 1: 文档解析与存储                    │
│  - 多格式解析 (见第四节)                    │
│  - RAG 分块+向量化 (异步)                   │
│  - 全文保留 (备查)                         │
└──────────────────┬───────────────────────┘
                   ▼
┌──────────────────────────────────────────┐
│  Step 2: LLM 自动生成教学大纲 (异步)        │
│  分析教材 → 提取章节目录 → 识别知识点        │
│  → 估算难度 → 推断依赖关系                  │
│  → 生成 exercises 建议                     │
│  → 输出结构化 YAML                         │
└──────────────────┬───────────────────────┘
                   ▼
┌──────────────────────────────────────────┐
│  Step 3: 教学运行时                        │
│  - 从生成的大纲中选择知识点                  │
│  - RAG 检索教材相关段落                     │
│  - 动态生成 teaching_hint (基于角色风格)     │
│  - 构建完整的教学 Prompt                   │
└──────────────────────────────────────────┘
```

**内置课程 vs 用户教材对比**：

| 字段 | 内置课程 (pre-authored) | 用户教材 (auto-generated) |
|------|----------------------|-------------------------|
| `knowledge_points` | 手动精心设计 | LLM 自动提取 |
| `teaching_hints` (per角色) | 手动编写 | **运行时动态生成** |
| `suggested_questions` | 手动编写 | LLM 自动生成 / 可选 |
| `exercises` | 手动设计 | LLM 自动生成 / 可选 |
| `difficulty` | 手动标定 | LLM 估算 |
| `prerequisites` | 手动定义依赖链 | LLM 提取依赖 |

---

## 四、文档解析与异常处理

### 4.1 格式支持矩阵

| 格式 | 解析库 | 优先级 | 备注 |
|------|--------|--------|------|
| `.pdf` | pdfplumber / PyMuPDF | P0 | 需检测扫描件 |
| `.docx` | python-docx | P0 | 提取段落+表格 |
| `.txt` | 原生 `open()` | P0 | 需编码检测 |
| `.md` / `.markdown` | 原生 `open()` | P1 | 提取 YAML front matter |
| `.epub` | ebooklib | P2 | 后续版本 |
| `.html` | BeautifulSoup | P2 | 后续版本 |

### 4.2 解析流程

```
上传文件
    │
    ▼
[1. 文件大小检查] → 超过 50MB: 413 Payload Too Large
    │
    ▼
[2. MIME 类型检查] → 不合法: 415 Unsupported Media Type
    │ (前端 accept + 后端 python-magic 双重校验)
    ▼
[3. Magic Number 校验] → 伪造扩展名: 400 Bad Request
    │ (PDF: %PDF-, DOCX: PK\x03\x04)
    ▼
[4. 文本编码检测] → 仅 txt/md, 使用 chardet
    │ → 失败 fallback UTF-8
    ▼
[5. 格式特化解析]
    ├── PDF → pdfplumber 提取文本
    │   ├── 检测到扫描件 → 提示需要 OCR
    │   ├── 加密文件 → 提示解密
    │   └── 损坏 → 错误提示
    ├── DOCX → python-docx 提取段落+表格
    │   ├── .doc 旧格式 → 提示转换
    │   └── 损坏 → 错误提示
    └── TXT/MD → 编码检测后读取
        ├── 空文件 → 提示
        └── YAML 头 → 提取为元数据
```

### 4.3 错误码枚举

| 错误码 | 含义 | 前端行为 |
|--------|------|----------|
| `FILE_TOO_LARGE` | 超过 50MB | 提示压缩或拆分 |
| `FORMAT_UNSUPPORTED` | 不支持的格式 | 列出支持的格式 |
| `MAGIC_MISMATCH` | 扩展名与内容不符 | 提示使用正确扩展名 |
| `PDF_ENCRYPTED` | PDF 有密码保护 | 提示解密 |
| `PDF_SCANNED` | 扫描件需要 OCR | 提示等待较久/需安装 OCR |
| `PDF_CORRUPTED` | 文件损坏 | 提示重新导出 |
| `DOC_OLD_FORMAT` | 旧 .doc 格式 | 提示转换为 .docx |
| `FILE_EMPTY` | 内容为空 | 提示检查文件 |
| `ENCODING_FAILED` | 编码识别失败 | 允许手动选择编码 |
| `TEXT_TOO_SHORT` | 提取文字 < 500字 | 提示可能为图片文档 |
| `PARSE_TIMEOUT` | 解析超时 (>30s) | 提示重试或拆分 |

### 4.4 统一响应格式

```json
// 成功
{
  "status": "ok",
  "material_id": "uuid-xxx",
  "meta": {
    "format": "pdf",
    "pages": 45,
    "char_count": 152000,
    "encoding": "utf-8",
    "parse_duration_ms": 1230
  }
}

// 失败
{
  "status": "error",
  "error_code": "PDF_ENCRYPTED",
  "message": "该PDF已加密，无法提取文本内容。请提供未加密的版本。",
  "suggestion": "可使用 Adobe Acrobat 或在线工具移除密码保护"
}
```

---

## 五、异步处理流水线与状态机

### 5.1 教材处理状态机

```
                    uploading          ← 上传中 (客户端进度条)
                         │
                         ▼
                     parsing            ← 格式检测+文本提取 (同步, 1-5s)
                      │
           ┌──────────┼──────────┐
           ▼                     ▼
        failed (解析失败)      parsing_ok (解析成功)
           │                     │
           │                     ▼
           │                  indexing          ← RAG 分块+向量化 (异步, 5-30s)
           │                     │
           │                     ▼
           │                  outlining         ← LLM 生成大纲 (异步, 30s-3min)
           │                     │
           │                     ▼
           │                  ready             ← 全部完成
```

### 5.2 分阶段可用性

```
教材状态         可用功能
────────────────────────────────────────────────
uploading       ❌ 不可用 (仍在传输)
parsing         ❌ 不可用 (同步等待完成)
indexed         ✅ 自由对话模式 (RAG检索原文，无结构化大纲)
outlining       ✅ 自由对话模式 + 大纲预览(生成中)
ready           ✅ 完整教学模式 (结构化大纲引导 + 练习题 + 进度追踪)
failed          ❌ 不可用 (需重新上传)
────────────────────────────────────────────────
```

**设计原则**：异步阶段立即解锁部分功能，自由对话不依赖大纲。

### 5.3 前端交互时序

```
用户上传《Python编程》PDF
    │
    ▼
┌─ [上传进度条] ──────────────────────────────┐
│  ████████████████████████ 100%               │
│  上传完成，正在解析文件...                      │
└──────────────────────────────────────────────┘
    │ (同步等待 1-2s)
    ▼
┌─ [解析完成] ────────────────────────────────┐
│  ✅ 解析成功                                  │
│  📄 共 45 页，15.2 万字                       │
│  📊 检测到 12 个章节结构                       │
│                                              │
│  [开始自由对话]  ← 立即可用!                   │
│  (基于教材内容的苏格拉底式提问)                 │
│                                              │
│  ⏳ 正在生成教学大纲...     [进度: 分析章节中]   │
│  (完成后将开启结构化教学模式)                   │
└──────────────────────────────────────────────┘
    │ (后台处理中，用户可自由对话)
    ▼
    30s-3min 后...
    ▼
┌─ [大纲生成完成] ────────────────────────────┐
│  🎉 教学大纲已生成！                          │
│  📋 共 3 个阶段，18 个知识点                   │
│  📅 建议学习周期：45 天                        │
│                                              │
│  [查看大纲]  [开始结构化教学]                  │
│  (当前自由对话模式仍然可用)                    │
└──────────────────────────────────────────────┘
```

### 5.4 WebSocket 状态推送

```json
{
  "type": "material.status_changed",
  "payload": {
    "material_id": "uuid-xxx",
    "status": "indexed",
    "progress": 100,
    "progress_message": "索引建立完成",
    "capabilities": {
      "free_chat": true,
      "structured_mode": false,
      "exercises": false,
      "progress_tracking": false
    }
  }
}
```

### 5.5 异常恢复

| 场景 | 处理方式 |
|------|---------|
| LLM 大纲生成超时 (3min) | `outlining` → `indexed` 降级，保留自由对话，提供重试 |
| LLM 返回格式不合法 | 重试 3 次 → 仍失败标记 `ready` 但无结构化大纲 |
| 后台任务中途服务器重启 | 扫描残留状态并重新入队 |
| 用户删除正在处理的教材 | 取消后台任务，清理临时数据 |
| 用户上传新版本替换 | 旧任务取消 → 新任务开始 → 状态重置 |

### 5.6 统一响应格式

```json
// GET /api/v1/materials/{id}/status
{
  "status": "outlining",
  "progress": 65,
  "progress_message": "正在生成练习题...",
  "capabilities": {
    "free_chat": true,
    "structured_mode": false,
    "exercises": false,
    "progress_tracking": false
  },
  "timeline": {
    "uploaded_at": "2025-01-15T10:00:00Z",
    "parsed_at": "2025-01-15T10:00:03Z",
    "indexed_at": "2025-01-15T10:00:25Z",
    "ready_at": null
  }
}
```

---

## 六、数据模型设计

### 6.1 新增 SQLite 模型

```sql
-- 教材状态追踪 (改造 materials 表)
ALTER TABLE materials ADD COLUMN
    status TEXT DEFAULT 'parsing',          -- 状态机字段
    error_code TEXT,                         -- 错误码
    source_syllabus_id INTEGER REFERENCES syllabuses(id),
    page_count INTEGER,
    char_count INTEGER;

-- 教学大纲 (新增)
CREATE TABLE syllabuses (
    id INTEGER PRIMARY KEY,
    material_id INTEGER REFERENCES materials(id),
    name TEXT NOT NULL,
    total_days INTEGER DEFAULT 90,
    content JSON NOT NULL,                   -- 完整 YAML 结构化数据
    generated_by TEXT DEFAULT 'llm',         -- "llm" | "manual"
    created_at DATETIME,
    updated_at DATETIME
);

-- 知识点 (新增)
CREATE TABLE knowledge_points (
    id INTEGER PRIMARY KEY,
    syllabus_id INTEGER REFERENCES syllabuses(id),
    point_id TEXT NOT NULL,                  -- 知识点唯一标识
    module_name TEXT,
    point_name TEXT NOT NULL,
    difficulty INTEGER DEFAULT 1,
    key_concepts JSON,                       -- ["概念A", "概念B"]
    teaching_hints JSON,                     -- 角色专属教学提示 (用户教材可为 null)
    suggested_questions JSON,
    exercises JSON,
    prerequisites JSON,
    sort_order INTEGER
);

-- 世界观状态 (新增)
CREATE TABLE world_states (
    id INTEGER PRIMARY KEY,
    current_day INTEGER DEFAULT 1,
    current_scene TEXT DEFAULT 'classroom',
    narrative_phase TEXT,
    global_flags JSON,                       -- {"final_exam_passed": false}
    created_at DATETIME,
    updated_at DATETIME
);

-- 角色运行时状态 (新增)
CREATE TABLE character_states (
    id INTEGER PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    current_mood REAL DEFAULT 0.7,
    trust_level REAL DEFAULT 0.5,
    relationship_tags JSON,
    last_interaction_at DATETIME
);

-- 学习进度 (新增)
CREATE TABLE learning_progress (
    id INTEGER PRIMARY KEY,
    knowledge_point_id TEXT,
    status TEXT DEFAULT 'locked',            -- locked/unlocked/learning/mastered
    mastery_level REAL DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    last_reviewed_at DATETIME,
    weak_areas JSON
);

-- 事件日志 (新增)
CREATE TABLE event_logs (
    id INTEGER PRIMARY KEY,
    event_type TEXT,                         -- time_based/condition_based/random
    event_id TEXT,
    trigger_context JSON,
    resolved BOOLEAN DEFAULT FALSE,
    resolution_data JSON,
    created_at DATETIME,
    resolved_at DATETIME
);
```

### 6.2 现有模型改造

```sql
-- 对话关联知识点与场景
ALTER TABLE conversations ADD COLUMN
    knowledge_point_id TEXT,                 -- 关联知识点
    scene_id TEXT,                           -- 关联场景
    narrative_context JSON;                  -- 叙事上下文
```

---

## 七、WebSocket 协议设计

### 7.1 消息类型

```
客户端 → 服务端:
┌─────────────────────────────────────────────────────┐
│ 类型               │ 描述                            │
├────────────────────┼─────────────────────────────────┤
│ chat.send          │ 发送对话消息                     │
│ chat.cancel        │ 取消当前生成                     │
│ scene.switch       │ 请求切换场景                     │
│ action.choose      │ 选择叙事分支选项                 │
│ state.sync         │ 请求完整状态同步                 │
│ ping               │ 心跳                            │
└─────────────────────────────────────────────────────┘

服务端 → 客户端:
┌─────────────────────────────────────────────────────┐
│ 类型               │ 描述                            │
├────────────────────┼─────────────────────────────────┤
│ chat.token         │ 流式对话 token                   │
│ chat.complete      │ 对话完成 (含完整响应)            │
│ event.trigger      │ 事件触发通知                     │
│ scene.change       │ 场景切换通知                     │
│ emotion.update     │ 角色情感变化                     │
│ progress.update    │ 学习进度更新                     │
│ time.advance       │ 时间推进 (天/阶段)              │
│ narrative.options  │ 叙事分支选项 (用户需选择)       │
│ state.full         │ 完整状态快照                     │
│ error              │ 错误信息                         │
│ pong               │ 心跳响应                         │
└─────────────────────────────────────────────────────┘
```

### 7.2 消息示例

```json
// 服务端推送事件
{
  "type": "event.trigger",
  "payload": {
    "event_id": "surprise_quiz",
    "title": "⚠️ 突发测验！",
    "description": "刻晴突然宣布今天有一个小测验...",
    "scene_change": "exam_room",
    "options": [
      {"id": "accept", "text": "接受挑战", "effect": {"mood_keqing": "+5"}},
      {"id": "negotiate", "text": "请求延期", "effect": {"trust_keqing": "-3"}}
    ]
  }
}

// 服务端推送情感更新
{
  "type": "emotion.update",
  "payload": {
    "character_id": "keqing",
    "mood": 0.85,
    "mood_delta": "+0.05",
    "cause": "学生正确回答了一道难题",
    "expression": "嘴角微微上扬，眼中闪过一丝满意"
  }
}

// 服务端推送进度更新
{
  "type": "progress.update",
  "payload": {
    "knowledge_point_id": "backpropagation",
    "status": "mastered",
    "mastery": 0.92,
    "current_day": 42,
    "next_point": "optimization_methods"
  }
}
```

---

## 八、引擎架构设计

### 8.1 引擎协作关系

```
┌──────────────────────────────────────────────────────┐
│                   NarrativeEngine                     │
│              (叙事编排引擎 - 总调度)                    │
│  接收 WS 消息 → 协调各引擎 → 组合响应 → 推送客户端      │
└───┬────────┬─────────┬─────────┬──────────┬──────────┘
    │        │         │         │          │
    ▼        ▼         ▼         ▼          ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐
│World │ │Char  │ │Event │ │Emot  │ │Teaching  │
│State │ │Eng.  │ │Eng.  │ │Eng.  │ │Eng.      │
│Eng.  │ │      │ │      │ │      │ │          │
└──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └────┬─────┘
   │        │        │        │           │
   ▼        ▼        ▼        ▼           ▼
┌──────────────────────────────────────────────────────┐
│              AssessmentEngine (考核引擎)               │
│  独立引擎，由叙事引擎在特定场景触发                      │
└──────────────────────────────────────────────────────┘
```

### 8.2 各引擎职责

**TeachingEngine (教学协作引擎)** — 核心引擎：

```python
class TeachingEngine:
    """
    决定"教什么"和"怎么教"
    """
    def get_next_teaching_point(
        self, progress, syllabus, character
    ) -> KnowledgePoint:
        """根据进度、大纲和角色，选择下一个教学知识点"""
        # 1. 从 syllabus 获取当前阶段应学模块
        # 2. 从 progress 找到第一个未掌握的 knowledge_point
        # 3. 检查前置依赖是否满足
        # 4. 返回知识点 + 角色专属 teaching_hint

    def build_teaching_prompt(
        self, point, character, scene, history, emotion
    ) -> str:
        """构建完整教学 Prompt"""
        # 1. 基础系统提示 (苏格拉底教学法)
        # 2. 角色人格 + 当前情感状态
        # 3. 场景氛围描述
        # 4. 知识点 teaching_hint (预编写 或 动态生成)
        # 5. 建议提问
        # 6. 历史对话摘要

    async def get_teaching_hint(self, point, character, rag_context):
        """运行时动态生成角色专属教学建议"""
        if point.teaching_hints:
            return point.teaching_hints[character.id]
        # 用户教材: 基于 RAG 检索内容 + 角色风格动态生成
```

**EmotionEngine (情感引擎)**：

```python
class EmotionEngine:
    """
    计算和更新角色的情感状态
    输入：事件、学生表现、时间流逝
    输出：情感值变化 + 叙事表达文本
    """
    def update(self, character_state, trigger_event):
        # 根据 event_sensitivity 计算情感变化
        # 考虑时间衰减
        # 生成情感变化的叙事描述文本
        # 如果跨过阈值，触发情感事件
```

**EventEngine (事件引擎)**：

```
触发条件三类：
1. time_based     → 到达特定天数触发 (如 Day 30: 阶段测验)
2. condition_based → 满足条件触发 (如 mastery > 0.8 AND trust > 0.6)
3. random          → 概率触发 (如每天 10% 概率触发随机事件)

事件驱动叙事分支：
用户选择 → 影响世界状态标志 → 改变未来事件触发条件
```

**WorldStateEngine (世界状态引擎)**：

```python
class WorldStateEngine:
    """
    维护：世界观状态 (天数、场景、全局标志)
    提供：时间推进、场景切换、状态快照
    """
    def advance_time(self, hours):
        # 推进时间 → 触发时间事件检查 → 更新场景氛围
```

**NarrativeEngine (叙事编排引擎)** — 总调度：

```python
class NarrativeEngine:
    """接收 WS 消息，协调各引擎，组合响应"""
    async def handle_chat_message(self, ws, user_message):
        # 1. TeachingEngine 构建 Prompt
        # 2. LLMProvider 流式生成
        # 3. 分析学生回答质量 → 更新学习进度
        # 4. EmotionEngine 更新角色情感
        # 5. EventEngine 检查是否触发事件
        # 6. WorldStateEngine 推进时间
        # 7. 组合多个 WS 消息推送客户端
```

---

## 九、前端叙事状态管理

```javascript
// stores/narrative.js - 前端叙事状态镜像
{
  // 世界状态
  world: {
    currentDay: 42,
    totalDays: 90,
    currentScene: 'classroom',
    narrativePhase: 'chapter_2',
    timeOfDay: 'morning'
  },

  // 角色状态 (精简摘要)
  characters: {
    'ganyu': { mood: 0.72, moodTrend: 'up', lastExpression: '温柔地微笑' },
    'keqing': { mood: 0.85, moodTrend: 'stable', lastExpression: '满意地点头' },
    'march7th': { mood: 0.91, moodTrend: 'up', lastExpression: '兴奋地拍手' }
  },

  // 学习进度
  progress: {
    currentPoint: 'backpropagation',
    status: 'learning',
    mastery: 0.45,
    completedPoints: 12,
    totalPoints: 45,
    weakAreas: ['链式法则', '梯度计算'],
    nextMilestone: { day: 45, event: '阶段测验' }
  },

  // 活跃事件
  activeEvents: [],

  // 叙事选项
  narrativeChoices: null
}
```

---

## 十、教学流程示例

```
用户打开系统 → [WS 连接] → 获取完整状态快照
    │
    ▼
[仪表盘] 显示当前进度、角色状态、时间线
    │
    ▼
[进入教室场景] → 叙事引擎根据大纲决定今日教学内容
    │
    ▼
[教学引擎] → 选择知识点 → 获取 teaching_hint → 构建 Prompt
    │
    ▼
[LLM 流式生成] → 推送 chat.token → 前端渲染
    │
    ▼
[学生回复] → 教学引擎分析回复质量
    │
    ├──→ [进度引擎] 更新 mastery_level
    │       └── 如果 mastery > 0.8 → progress.update (知识点掌握)
    │
    ├──→ [情感引擎] 更新角色情感
    │       └── emotion.update (角色的情感表达)
    │
    ├──→ [事件引擎] 检查触发条件
    │       └── 如果 Day 30 且 mastery < 0.5 → event.trigger (补课警告)
    │
    └──→ [叙事引擎] 组合所有更新 → 推送客户端
    │
    ▼
[继续教学循环] 或 [场景切换] 或 [触发考核]
```

---

## 十一、迁移路径

### Phase 1: 基础设施层

| 任务 | 说明 |
|------|------|
| 建立 `content/` 目录结构 | syllabus.yaml + 首批 modules YAML |
| 新增 SQLite 模型 | world_states, character_states, learning_progress, events, syllabus, knowledge_point |
| 文档解析器 | pdf_parser, docx_parser, text_parser + 错误码体系 |
| Repository 扩展 | 为新模型添加 Repository |
| WebSocket 基础设施 | ws.py + ws_protocol.py + useWebSocket.js |
| 前端新页面骨架 | Timeline, Scene, Exam, Curriculum |
| 教材上传改造 | 多格式支持 + 状态机 + 异步流水线 |

### Phase 2: 内容与引擎层

| 任务 | 说明 |
|------|------|
| 编写完整课程内容 | 至少 2 个 phase 的知识模块 YAML (含 teaching_hints) |
| TeachingEngine | 知识点选择 + Prompt 构建 + teaching_hint 动态生成 |
| EmotionEngine | 情感计算与衰减逻辑 |
| EventEngine | 时间/条件/随机事件触发器 |
| WorldStateEngine | 时间推进 + 场景管理 |
| RAG 集成 | LlamaIndex + FAISS 最小实现 |

### Phase 3: 集成与叙事层

| 任务 | 说明 |
|------|------|
| NarrativeEngine | 总调度引擎 (协调所有引擎) |
| AssessmentEngine | 考核模式 (测验/辩论赛) |
| 前端 Narrative State Manager | narrative.js Pinia store |
| Timeline 可视化 | 90天进度条 + 里程碑标记 |
| 角色状态卡片 | 动态情感/表情展示 |
| 场景切换 UI | 场景描述 + 转场动画 |
| 事件通知系统 | 事件弹窗 + 叙事选项 |

### Phase 4: 打磨与发布

| 任务 | 说明 |
|------|------|
| 完善所有课程内容 | 90天完整大纲 |
| 性能优化 | WebSocket 连接管理、消息压缩 |
| 测试 | 单元测试 + 集成测试 + 叙事流程 E2E 测试 |
| Docker 部署更新 | 更新 docker-compose 适配新架构 |
| Windows 打包 | 更新 PyInstaller spec |

---

## 十二、可复用的现有代码

| 模块 | 复用方式 |
|------|---------|
| `LLMProvider` (chat_service.py) | 迁移到 `app/llm/provider.py`，接口不变 |
| `Repository` + `UoW` (repositories/) | 保留模式，新增叙事模型 Repository |
| `ModelConfig` CRUD | 完整保留 |
| `FileUploadService` | 保留用于头像/背景上传 |
| `concurrency.py` | WebSocket session 管理可参考其锁设计 |
| `config.py` / `database.py` | 保留基础设施 |
| 前端 Settings.vue | 完整保留 |
| 前端 Markdown 渲染管线 (Chat.vue) | 迁移到新的 Chat.vue |
| 前端 `api/index.js` (Axios) | REST 部分保留，新增 WebSocket composable |
| 测试基础设施 (pytest, conftest) | 扩展而非重写 |

---

## 十三、关键设计决策

| 决策 | 选项 | 选择 | 理由 |
|------|------|------|------|
| 课程存储格式 | YAML 文件 vs 数据库表 | **YAML 文件** | 课程内容由设计者编写，非运行时频繁修改 |
| WebSocket 库 | `websockets` vs FastAPI 内置 | **FastAPI 内置** | 减少依赖，与现有框架统一 |
| 角色状态持久化 | 每次变化写 DB vs 内存+定时落盘 | **内存+定时落盘** | 减少 DB 写入压力，丢失少量状态可接受 |
| 前端 Markdown 渲染 | marked + KaTeX vs MDX + React | **marked + KaTeX** | 已在 Chat.vue 中验证可行 |
| 多用户支持 | MVP 单用户 vs Phase 2 多用户 | **MVP 单用户** | 降低复杂度，状态模型 + user_id 即可扩展 |
| 大纲生成 | 同步 (用户等待) vs 异步 (即时可用) | **异步 + 降级可用** | 解析完即可自由对话，大纲后台生成 |
| RAG 方案 | FAISS (最小) vs RAGFlow (完整) | **FAISS MVP** | 通过 BaseRAGProvider 抽象，可后续升级至 RAGFlow |
