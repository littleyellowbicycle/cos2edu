# 苏格拉底AI教学系统 - 重新设计方案

> 基于 `design.md` 理念，对当前项目进行叙事驱动架构重构的完整方案。
> v2: 融入6条针对性优化建议（MVP剥离、Context Budget、知识图、状态落盘分级、人工确认大纲、WS重连对账）。

---

## 一、核心理念变化

| 维度 | 当前 | 新设计 |
|------|------|--------|
| **教学范式** | 自由对话 + 手动上传教材 | 结构化课程体系驱动，引擎按大纲规划教学路径 |
| **通信方式** | REST + SSE 流式 | **WebSocket 为主** (对话/事件/状态同步)，REST 为辅 (历史查询/配置) |
| **角色系统** | 静态人格描述 | 动态角色：情感引擎 + 关系系统 + 差异化教学提示 |
| **叙事驱动** | 无 | 世界观状态、时间线推进、事件触发、场景切换 |
| **内容来源** | 仅支持用户上传 | 双轨制：内置精品课程 (预编写 YAML) + 用户上传教材 (LLM 自动提取大纲) |
| **数据存储** | SQLite ORM (全关系型) | YAML 文件 (课程内容) + 内存知识图 (依赖 DAG) + SQLite (运行时状态) 三层存储 |
| **前端状态** | Pinia store (CRUD) | **Narrative State Manager** 维护轻量世界状态镜像，WS 重连自动对账 |
| **架构风格** | 分层 CRUD | **领域引擎模式** (WorldState / Character / Event / Emotion / Teaching / Assessment Engines) |
| **Prompt 构建** | 简单拼接 | **Context Budget 机制**，硬性分配 token 预算 |
| **大纲生成** | 无 | 异步 LLM 生成 + 人工确认环节 |

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
│   │   │   ├── prompt_builder.py        # Prompt 构建器 (含 Context Budget)
│   │   │   └── context_budget.py        # 上下文预算分配器
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
│   │   ├── graph/                       # 知识图谱 (新增)
│   │   │   ├── __init__.py
│   │   │   └── knowledge_graph.py       # 内存 DAG，启动时从 YAML 加载
│   │   ├── state/                       # 状态管理 (新增)
│   │   │   ├── __init__.py
│   │   │   └── state_manager.py         # 分级落盘：Critical 立即写，Soft 定时批量
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
│   │   │   ├── material_pipeline.py     # 教材处理流水线 (解析→索引→大纲→人审)
│   │   │   └── task_registry.py         # 内存任务状态追踪
│   │   └── core/                        # 基础设施 (保留)
│   │       ├── config.py
│   │       ├── database.py
│   │       ├── limiter.py
│   │       └── ...
│   ├── models/                          # SQLAlchemy ORM (新增叙事相关模型)
│   │   ├── base.py
│   │   ├── character.py
│   │   ├── material.py                  # 改造：新增状态机字段 + review_status
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
│       │   ├── Curriculum.vue         # 课程进度 + 大纲审核 (新增)
│       │   └── Settings.vue           # 配置 (保留)
│       ├── stores/
│       │   ├── narrative.js           # 叙事状态管理 (新增，核心)
│       │   ├── chat.js                # 聊天状态
│       │   └── settings.js            # 配置状态
│       ├── composables/
│       │   ├── useWebSocket.js        # WebSocket 连接管理 (含重连+对账)
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

用户上传任意教材，系统通过 LLM 自动提取结构化大纲，**经人工确认后**进入 ready 状态。

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
│  Step 3: 人工确认 (新增！)                  │
│  状态变为 pending_review                    │
│  前端展示生成的大纲                          │
│  用户可以：                                 │
│  ✅ 确认 → ready (完整教学)                 │
│  ✏️ 编辑微调 → 重新 pending_review          │
│  ❌ 放弃大纲 → 降级为 indexed (自由对话)     │
└──────────────────┬───────────────────────┘
                   ▼
┌──────────────────────────────────────────┐
│  Step 4: 教学运行时                        │
│  - 从确认后的大纲中选择知识点                │
│  - RAG 检索教材相关段落                     │
│  - 动态生成 teaching_hint (基于角色风格)     │
│  - 构建含 Context Budget 的完整 Prompt    │
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

### 3.3 知识依赖图 (内存 DAG)

YAML 中的 `prerequisites` 字段在系统启动时加载为内存 DAG 结构，TeachingEngine 基于图进行推导，避免每次查询解析 YAML。

```python
# backend/app/graph/knowledge_graph.py
class KnowledgeGraph:
    """启动时从 YAML 加载，常驻内存的知识点依赖图"""

    def __init__(self):
        self._graph: dict[str, set[str]] = {}   # point_id -> set(prerequisite_ids)
        self._point_meta: dict[str, dict] = {}    # point_id -> YAML 元数据

    def load_from_yaml(self, modules_dir: str):
        """扫描所有 YAML，构建邻接表"""
        for module_file in Path(modules_dir).glob("*.yaml"):
            module = yaml.safe_load(module_file.read_text(encoding="utf-8"))
            for point in module.get("knowledge_points", []):
                pid = point["id"]
                self._graph[pid] = set(point.get("prerequisites", []))
                self._point_meta[pid] = point

    def get_next_unlocked(self, mastered: set[str]) -> list[str]:
        """返回所有前置已满足的、未掌握的知识点"""
        return [
            pid for pid, deps in self._graph.items()
            if pid not in mastered and deps.issubset(mastered)
        ]

    def get_learning_path(self, mastered: set[str]) -> list[str]:
        """拓扑排序，返回推荐学习路径"""
        # Kahn's algorithm: 逐步解锁前置已满足的知识点

    def get_point(self, point_id: str) -> dict | None:
        """获取知识点元数据"""
        return self._point_meta.get(point_id)

    def reload(self):
        """热重载 YAML (开发/调试用)"""
        self._graph.clear()
        self._point_meta.clear()
        self.load_from_yaml(...)
```

用户上传教材生成的大纲同样加载到图中，与内置课程合并。

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

## 五、异步处理流水线与状态机（含人工确认）

### 5.1 教材处理状态机

```
                    uploading          ← 上传中 (客户端进度条)
                         │
                         ▼
                     parsing            ← 格式检测+文本提取 (同步, 1-5s)
                      │
           ┌──────────┼──────────┐
           ▼                     ▼
        failed (解析失败)      parsed_ok
           │                     │
           │                     ▼
           │                  indexing          ← RAG 分块+向量化 (异步, 5-30s)
           │                     │
           │                     ▼
           │                  indexed            ← 自由对话可用
           │                     │
           │                     ▼
           │                  outlining          ← LLM 生成大纲 (异步, 30s-3min)
           │                     │
           │                     ▼
           │               pending_review       ← 等待人工确认 (新增！)
           │                  │
           │        ┌─────────┼─────────┐
           │        ▼         ▼         ▼
           │     confirm    edit       reject
           │        │     (微调后       │
           │        │      重新review)  │
           │        ▼         ▼         ▼
           │      ready      pending   indexed (降级，仅自由对话)
           │               _review
           │
           ▼
        failed (不可恢复)
```

### 5.2 分阶段可用性

```
教材状态              可用功能
────────────────────────────────────────────────────
uploading            ❌ 不可用 (仍在传输)
parsing              ❌ 不可用 (同步等待完成)
indexed              ✅ 自由对话模式 (RAG检索原文，无结构化大纲)
outlining            ✅ 自由对话模式 + "大纲生成中" 提示
pending_review       ✅ 自由对话模式 + 大纲审核页面 (新增！)
ready                ✅ 完整教学模式 (结构化大纲引导 + 练习题 + 进度追踪)
failed               ❌ 不可用 (需重新上传)
────────────────────────────────────────────────────
```

**设计原则**：
- 异步阶段立即解锁部分功能，自由对话不依赖大纲
- LLM 生成的大纲必须经人工确认后才进入 ready，防止幻觉依赖链导致教学混乱

### 5.3 大纲审核页面

```
┌─ [大纲审核] ──────────────────────────────┐
│  📋 《Python编程入门》 教学大纲预览           │
│                                            │
│  Phase 1: 基础 (第1-15天)                   │
│  ├── 变量与数据类型 ⭐难度1                   │
│  ├── 控制流 ⭐难度2                         │
│  └── 函数 ⭐难度2                           │
│                                            │
│  Phase 2: 进阶 (第16-30天)                   │
│  ├── 面向对象 ⭐难度3                       │
│  ├── 异常处理 ⭐难度2                       │
│  └── 文件操作 ⭐难度2                       │
│                                            │
│  ⚠️ AI 生成的依赖关系可能不完全准确           │
│                                            │
│  [✅ 确认开始学习]  [✏️ 编辑微调]  [❌ 放弃大纲]│
└────────────────────────────────────────────┘
```

MaterialStatus 枚举更新：

```python
class MaterialStatus(str, Enum):
    UPLOADING = "uploading"
    PARSING = "parsing"
    PARSED = "parsed"
    INDEXING = "indexing"
    INDEXED = "indexed"            # ← 自由对话可用
    OUTLINING = "outlining"
    PENDING_REVIEW = "pending_review"  # ← 等待人工确认
    READY = "ready"                # ← 完整教学模式
    FAILED = "failed"
```

### 5.4 前端交互时序

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
┌─ [大纲待审核] ──────────────────────────────┐  ← 新增！
│  📋 教学大纲已生成，请确认：                     │
│                                              │
│  Phase 1: 基础 (15天)                        │
│  ├── 变量与数据类型 [难度1] 前置: 无           │
│  ├── 控制流 [难度2] 前置: 变量                 │
│  └── 函数 [难度2] 前置: 控制流                 │
│                                              │
│  ⚠️ 建议检查依赖关系是否合理                    │
│                                              │
│  [✅ 确认开始学习]  [✏️ 编辑微调]  [❌ 放弃大纲]│
└──────────────────────────────────────────────┘
    │
    ▼ (用户点击"确认")
    ▼
┌─ [结构化教学就绪] ──────────────────────────┐
│  🎉 结构化教学模式已开启！                     │
│  📋 共 3 个阶段，18 个知识点                   │
│  📅 建议学习周期：45 天                        │
│                                              │
│  [开始学习]                                  │
└──────────────────────────────────────────────┘
```

### 5.5 WebSocket 状态推送

```json
{
  "type": "material.status_changed",
  "payload": {
    "material_id": "uuid-xxx",
    "status": "pending_review",
    "progress": 100,
    "progress_message": "大纲已生成，等待确认",
    "capabilities": {
      "free_chat": true,
      "structured_mode": false,
      "exercises": false,
      "progress_tracking": false
    }
  }
}
```

### 5.6 异常恢复

| 场景 | 处理方式 |
|------|---------|
| LLM 大纲生成超时 (3min) | `outlining` → `indexed` 降级，保留自由对话，提供重试 |
| LLM 返回格式不合法 | 重试 3 次 → 仍失败标记 `pending_review` 但提示大纲生成失败，用户可手动编辑 |
| 用户拒绝大纲 | 回到 `indexed` 状态，仅自由对话可用 |
| 用户编辑大纲后确认 | 重新进入 `pending_review`，可多次编辑 |
| 后台任务中途服务器重启 | 扫描残留状态并重新入队 |
| 用户删除正在处理的教材 | 取消后台任务，清理临时数据 |
| 用户上传新版本替换 | 旧任务取消 → 新任务开始 → 状态重置 |

### 5.7 状态响应格式

```json
// GET /api/v1/materials/{id}/status
{
  "status": "pending_review",
  "progress": 100,
  "progress_message": "大纲已生成，等待确认",
  "capabilities": {
    "free_chat": true,
    "structured_mode": false,
    "exercises": false,
    "progress_tracking": false
  },
  "syllabus_preview": {
    "total_phases": 3,
    "total_points": 18,
    "estimated_days": 45,
    "phases": [
      {"name": "基础", "points": 6, "days": "1-15"},
      {"name": "进阶", "points": 7, "days": "16-30"},
      {"name": "实战", "points": 5, "days": "31-45"}
    ]
  },
  "timeline": {
    "uploaded_at": "2025-01-15T10:00:00Z",
    "parsed_at": "2025-01-15T10:00:03Z",
    "indexed_at": "2025-01-15T10:00:25Z",
    "outlined_at": "2025-01-15T10:02:30Z",
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
    review_status TEXT DEFAULT NULL,        -- 'pending' | 'approved' | 'rejected'
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
    review_notes TEXT,                        -- 用户审核备注
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

## 七、Prompt 工程架构：Context Budget 机制

### 7.1 上下文预算分配

TeachingEngine 的 Prompt 构建不是简单拼接，而是基于 Context Budget 机制，硬性分配 token 预算：

```
总预算: 4096 tokens (可配置)
┌─────────────────────────────────────────────┐
│ 📍 System Core (强制, 200 tokens)            │
│   - 苏格拉底教学法核心原则                     │
│   - 场景硬约束 <rule>...</rule>              │
│   - 当前场景 + 允许动作                       │
│   ├─ <rule>你必须严格遵循当前场景              │
│   │  [{scene_id}]的允许动作                   │
│   │  [{allowed_actions}]，绝不能越界。</rule> │
│   └─ <rule>不在考核场景时，不能主动发起测验。</rule>│
├─────────────────────────────────────────────┤
│ 🎭 Character Persona (强制, 300 tokens)      │
│   - 角色人格描述                              │
│   - 当前情感状态摘要                           │
│   - 教学风格                                  │
├─────────────────────────────────────────────┤
│ 📚 Teaching Context (强制, 1000 tokens)      │
│   - 当前知识点 teaching_hint                  │
│   - 核心概念列表                               │
│   - 建议提问                                  │
│   - RAG 检索段落 (或 教材原文截取)              │
├─────────────────────────────────────────────┤
│ 💬 History (动态, 剩余空间 ≈2596 tokens)      │
│   - 最近 N 轮对话摘要                          │
│   - 本轮之前的历史压缩                         │
│   - 根据剩余 token 数动态截断                  │
└─────────────────────────────────────────────┘
```

### 7.2 ContextBudget 实现

```python
# backend/app/llm/context_budget.py
class ContextBudget:
    """上下文预算分配器"""

    def __init__(self, total_tokens: int = 4096):
        self.total = total_tokens
        self.allocations = {
            "system_core": 200,       # 强制
            "character_persona": 300,  # 强制
            "teaching_context": 1000, # 强制
            # history = total - 以上三项
        }

    @property
    def history_budget(self) -> int:
        """动态剩余预算"""
        fixed = sum(self.allocations.values())
        return max(200, self.total - fixed)  # 保底 200 tokens

    def build_prompt(
        self,
        system_core: str,
        character_persona: str,
        character_emotion: str,
        scene_id: str,
        allowed_actions: list[str],
        teaching_hint: str,
        key_concepts: list[str],
        suggested_questions: list[str],
        rag_context: str,
        history: list[dict],
    ) -> list[dict]:
        """按预算构建完整的 messages 数组"""

        # 1. System Core (硬约束)
        system = self._truncate(system_core, self.allocations["system_core"])
        scene_rule = (
            f"<rule>你必须严格遵循当前场景[{scene_id}]的"
            f"允许动作{allowed_actions}，绝不能越界。</rule>"
        )
        system += f"\n{scene_rule}"

        # 2. Character (强制)
        char = f"{character_persona}\n当前情感: {character_emotion}"
        char = self._truncate(char, self.allocations["character_persona"])

        # 3. Teaching Context (强制，含 RAG)
        teaching = f"教学提示: {teaching_hint}\n核心概念: {key_concepts}"
        if suggested_questions:
            teaching += f"\n建议提问: {suggested_questions}"

        rag_budget = self.allocations["teaching_context"] - self._estimate_tokens(teaching)
        if rag_budget > 100 and rag_context:
            rag_context = self._truncate(rag_context, rag_budget)
            teaching += f"\n\n参考资料:\n{rag_context}"

        teaching = self._truncate(teaching, self.allocations["teaching_context"])

        # 4. History (动态)
        combined_system = f"{system}\n\n{char}\n\n{teaching}"
        messages = [{"role": "system", "content": combined_system}]

        history_budget = self.history_budget
        used = 0
        for msg in reversed(history):
            tokens = self._estimate_tokens(msg["content"])
            if used + tokens > history_budget:
                break
            messages.insert(-1 if messages[-1]["role"] == "user" else len(messages), msg)
            used += tokens

        return messages

    def _truncate(self, text: str, max_tokens: int) -> str:
        """按 token 预算截断文本"""
        # 简单估算：中文约 1.5 字/token，英文约 4 字符/token
        # 实际可用 tiktoken 精确计算
        ...

    def _estimate_tokens(self, text: str) -> int:
        """估算文本 token 数"""
        ...
```

---

## 八、状态落盘策略：分级持久化

### 8.1 状态分级

| 状态类别 | 示例 | 落盘策略 | 可丢失？ |
|----------|------|----------|----------|
| **Critical** | knowledge_point mastery 变更 (learning→mastered) | **立即异步写 DB** | ❌ 不可丢失 |
| **Critical** | scene 切换 | **立即异步写 DB** | ❌ 不可丢失 |
| **Critical** | narrative choice (用户选择) | **立即异步写 DB** | ❌ 不可丢失 |
| **Critical** | syllabus review_status 变更 | **立即异步写 DB** | ❌ 不可丢失 |
| **Soft** | mood 变化 (0.7 → 0.72) | **定时批量** (每60s 或 每10次变更) | ✅ 可丢失最近几条 |
| **Soft** | trust_level 微调 | **定时批量** (每60s) | ✅ 可容忍少量丢失 |
| **Soft** | current_day 推进 | **定时落盘** (每5min) | ✅ 重启后从上次落盘点恢复 |

### 8.2 StateManager 实现

```python
# backend/app/state/state_manager.py
class StateManager:
    """分级状态落盘管理器"""

    CRITICAL_EVENTS = {
        'mastery_change', 'scene_change',
        'narrative_choice', 'review_status_change'
    }
    BATCH_SIZE = 10           # Soft 状态缓冲区大小
    FLUSH_INTERVAL = 60       # Soft 状态定时落盘间隔 (秒)

    def __init__(self, uow_factory):
        self._uow_factory = uow_factory
        self._soft_buffer: list[tuple] = []
        self._lock = asyncio.Lock()

    async def update(self, event_type: str, data: dict):
        """更新状态，根据事件级别决定落盘策略"""
        if event_type in self.CRITICAL_EVENTS:
            await self._persist_immediately(event_type, data)
        else:
            await self._buffer_for_batch(event_type, data)

    async def _persist_immediately(self, event_type: str, data: dict):
        """Critical 状态：立即异步写入 DB"""
        async with self._uow_factory() as uow:
            # 根据 event_type 分发到对应 repository
            if event_type == 'mastery_change':
                await uow.learning_progress.update_mastery(
                    data['point_id'], data['mastery'], data['status']
                )
            elif event_type == 'scene_change':
                await uow.world_state.update_scene(
                    data['scene_id']
                )
            elif event_type == 'narrative_choice':
                await uow.world_state.set_flag(
                    data['flag_key'], data['flag_value']
                )
            elif event_type == 'review_status_change':
                await uow.materials.update_review_status(
                    data['material_id'], data['review_status']
                )

    async def _buffer_for_batch(self, event_type: str, data: dict):
        """Soft 状态：缓冲，达到 batch_size 或定时器触发时批量写入"""
        async with self._lock:
            self._soft_buffer.append((event_type, data, datetime.now()))
            if len(self._soft_buffer) >= self.BATCH_SIZE:
                await self._flush_soft_buffer()

    async def _flush_soft_buffer(self):
        """批量写入 Soft 状态"""
        if not self._soft_buffer:
            return
        async with self._uow_factory() as uow:
            for event_type, data, ts in self._soft_buffer:
                if event_type == 'mood_change':
                    await uow.character_state.update_mood(
                        data['character_id'], data['mood']
                    )
                elif event_type == 'trust_change':
                    await uow.character_state.update_trust(
                        data['character_id'], data['trust']
                    )
                elif event_type == 'time_advance':
                    await uow.world_state.advance_day(
                        data['current_day']
                    )
        self._soft_buffer.clear()

    async def start_periodic_flush(self):
        """启动定时落盘 (应用启动时调用)"""
        while True:
            await asyncio.sleep(self.FLUSH_INTERVAL)
            await self._flush_soft_buffer()

    async def shutdown_flush(self):
        """应用关闭时，强制落盘所有缓冲状态"""
        await self._flush_soft_buffer()
```

### 8.3 启动恢复策略

```
服务器启动
    │
    ▼
[1] 从 DB 加载最后落盘的世界状态 (current_day 可能偏旧)
    │
    ▼
[2] 从 DB 加载所有角色状态 (mood/trust 可能偏旧)
    │
    ▼
[3] 从 content/*.yaml 加载知识图谱到内存
    │
    ▼
[4] 从 DB 加载学习进度 (Critical, 一定是最新的)
    │
    ▼
[5] 补偿：检查 event_log 中是否有未恢复状态变更
    │   (可选：通过 Critical 事件日志回放)
    │
    ▼
[6] 启动 StateManager 定时落盘任务
    │
    ▼
[7] 开始接受请求
```

---

## 九、WebSocket 协议设计（含重连对账）

### 9.1 消息类型

```
客户端 → 服务端:
┌─────────────────────────────────────────────────────┐
│ 类型               │ 描述                            │
├────────────────────┼─────────────────────────────────┤
│ chat.send          │ 发送对话消息                     │
│ chat.cancel        │ 取消当前生成                     │
│ scene.switch       │ 请求切换场景                     │
│ action.choose      │ 选择叙事分支选项                 │
│ state.sync         │ 请求完整状态同步 (重连对账用)      │
│ syllabus.confirm   │ 确认大纲 (传入 material_id)       │
│ syllabus.edit      │ 编辑大纲 (传入修改数据)            │
│ syllabus.reject    │ 拒绝大纲 (传入 material_id)       │
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
│ state.full         │ 完整状态快照 (重连对账用)         │
│ material.status_changed │ 教材状态变更通知            │
│ error              │ 错误信息                         │
│ pong               │ 心跳响应                         │
└─────────────────────────────────────────────────────┘
```

### 9.2 WebSocket 重连与状态对账

前端 `useWebSocket.js` 必须设计健壮的重连逻辑。**每次 WS 断开重连后，前端自动发送 `state.sync` 请求，拿回最新的 `state.full` 快照，强制覆盖前端 `narrative.js` store**，防止断线期间的增量推送丢失导致的状态不一致。

```javascript
// composables/useWebSocket.js
class NarrativeWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectDelay = 30000; // 最大退避 30s

  connect(url: string) {
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      // ✅ 关键：连接建立后立即请求完整状态快照
      this.send({ type: 'state.sync' });
    };

    this.ws.onclose = () => {
      // 指数退避重连: 1s, 2s, 4s, 8s, 16s, 30s, 30s...
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), this.maxReconnectDelay);
      this.reconnectAttempts++;
      setTimeout(() => this.connect(url), delay);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      // onclose 会被紧接着触发，重连逻辑在那里处理
    };

    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      this.handleMessage(msg);
    };
  }

  private handleMessage(msg: any) {
    switch (msg.type) {
      case 'state.full':
        // ✅ 强制覆盖前端 store，解决断线期间丢失的增量推送
        useNarrativeStore().overwriteState(msg.payload);
        break;
      case 'chat.token':
        // 流式 token 处理
        break;
      case 'material.status_changed':
        // 教材状态变更 (如大纲生成完成)
        break;
      // ... 其他消息类型
    }
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}
```

后端处理 `state.sync`：

```python
# backend/app/api/v1/ws.py
@websocket.on("state.sync")
async def handle_state_sync(ws, payload):
    """返回完整快照：世界状态 + 所有角色状态 + 学习进度 + 活跃事件"""
    snapshot = await narrative_engine.get_full_snapshot()
    await ws.send({
        "type": "state.full",
        "payload": snapshot
    })
```

### 9.3 消息示例

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

## 十、引擎架构设计

### 10.1 引擎协作关系

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

### 10.2 各引擎职责

**TeachingEngine (教学协作引擎)** — 核心引擎：

```python
class TeachingEngine:
    """
    决定"教什么"和"怎么教"
    使用 KnowledgeGraph 选择知识点
    使用 ContextBudget 构建 Prompt
    """
    def __init__(self, knowledge_graph: KnowledgeGraph, budget: ContextBudget):
        self.graph = knowledge_graph
        self.budget = budget

    def get_next_teaching_point(
        self, mastered_points: set[str], current_phase: str
    ) -> KnowledgePoint | None:
        """根据已掌握知识点和当前阶段，选择下一个教学知识点"""
        # 1. 从 syllabus 获取当前阶段的模块
        # 2. 从 KnowledgeGraph 获取所有前置已满足的未掌握知识点
        unlocked = self.graph.get_next_unlocked(mastered_points)
        # 3. 优先选择当前阶段内的知识点
        # 4. 返回知识点

    def build_teaching_prompt(
        self, point, character, scene, history, emotion, rag_context
    ) -> list[dict]:
        """使用 ContextBudget 构建完整教学 Prompt"""
        return self.budget.build_prompt(
            system_core=SYSTEM_CORE_PROMPT,
            character_persona=character.personality,
            character_emotion=emotion.summary(),
            scene_id=scene.id,
            allowed_actions=scene.allowed_actions,
            teaching_hint=self._get_hint(point, character),
            key_concepts=point.key_concepts,
            suggested_questions=point.suggested_questions,
            rag_context=rag_context,
            history=history,
        )

    async def _get_hint(self, point, character) -> str:
        """获取教学提示：内置课程直接取，用户教材动态生成"""
        if point.teaching_hints:
            return point.teaching_hints.get(character.id, "")
        # 用户教材: 基于 RAG 检索内容 + 角色风格动态生成
        return await self._generate_hint(point, character)
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
        # 推进时间
        # 检查时间事件 (Critical: 立即落盘当日变更)
        # 更新场景氛围 (如接近考试日，紧张感上升)
```

**NarrativeEngine (叙事编排引擎)** — 总调度：

```python
class NarrativeEngine:
    """接收 WS 消息，协调各引擎，组合响应"""
    async def handle_chat_message(self, ws, user_message):
        # 1. TeachingEngine 构建 Prompt (使用 ContextBudget)
        # 2. LLMProvider 流式生成
        # 3. 分析学生回答质量 → 更新学习进度 (Critical: 立即落盘)
        # 4. EmotionEngine 更新角色情感 (Soft: 缓冲落盘)
        # 5. EventEngine 检查是否触发事件
        # 6. WorldStateEngine 推进时间 (Soft: 定时落盘)
        # 7. 组合多个 WS 消息推送客户端
```

---

## 十一、前端叙事状态管理

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
  narrativeChoices: null,

  // WS 连接状态 (对账相关)
  connectionState: 'connected', // connected | reconnecting | disconnected
  lastSyncAt: null              // 上次完整同步时间
}
```

```javascript
// stores/narrative.js - 关键方法
import { defineStore } from 'pinia'

export const useNarrativeStore = defineStore('narrative', {
  state: () => ({ /* ...如上... */ }),

  actions: {
    // ✅ 关键：状态对账，强制覆盖
    overwriteState(snapshot) {
      this.world = snapshot.world
      this.characters = snapshot.characters
      this.progress = snapshot.progress
      this.activeEvents = snapshot.activeEvents
      this.narrativeChoices = snapshot.narrativeChoices
      this.lastSyncAt = new Date()
    },

    // 增量更新 (正常 WS 推送时使用)
    updateEmotion(payload) {
      this.characters[payload.character_id] = {
        ...this.characters[payload.character_id],
        mood: payload.mood,
        moodTrend: payload.mood_delta > 0 ? 'up' : payload.mood_delta < 0 ? 'down' : 'stable',
        lastExpression: payload.expression
      }
    },

    updateProgress(payload) { /* ... */ },
    advanceTime(payload) { /* ... */ },
    // ...
  }
})
```

---

## 十二、教学流程示例

```
用户打开系统 → [WS 连接] → 发送 state.sync → 收到 state.full
    │
    ▼
[仪表盘] 显示当前进度、角色状态、时间线
    │
    ▼
[进入教室场景] → 叙事引擎根据大纲决定今日教学内容
    │
    ▼
[教学引擎] → KnowledgeGraph 选知识点 → ContextBudget 构建 Prompt
    │
    ▼
[LLM 流式生成] → 推送 chat.token → 前端渲染
    │
    ▼
[学生回复] → 教学引擎分析回复质量
    │
    ├──→ [进度引擎] 更新 mastery_level (Critical: 立即落盘)
    │       └── 如果 mastery > 0.8 → progress.update (知识点掌握)
    │
    ├──→ [情感引擎] 更新角色情感 (Soft: 缓冲)
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

## 十三、迁移路径（修订版：更彻底的 MVP 剥离）

### Phase 1.0 — 核心通路 (最小叙事闭环)

> **目标**：跑通"结构化教学 + 场景切换"的完整闭环。砍掉情感、事件、RAG。

| 任务 | 说明 |
|------|------|
| 项目骨架 | 新目录结构 (engines/, graph/, parsers/, state/, llm/, tasks/) |
| 内置课程 YAML | 编写 1-2 个模块 YAML (含 knowledge_points + teaching_hints + prerequisites) |
| KnowledgeGraph | 启动时从 YAML 构建 DAG，提供拓扑排序+前置依赖查询 |
| TeachingEngine | 从 KnowledgeGraph 选知识点 + ContextBudget 构建 Prompt |
| ContextBudget | 上下文预算分配器 (system 200 + character 300 + teaching 1000 + history 动态) |
| WorldStateEngine | 最小实现：当前天数 + 当前场景 + 全局标志 |
| WebSocket 基础 | chat.send/token/complete + state.sync/state.full + ping/pong |
| WS 重连对账 | useWebSocket.js 指数退避重连 + 重连后 state.sync 强制覆盖 |
| 前端 Chat.vue | WS 流式聊天 + Markdown 渲染 (复用现有) |
| 前端 Curriculum.vue | 内置课程大纲查看 + 当前知识点进度 |
| 分级落盘 | StateManager: mastery/scene Critical 立即落盘, 其他缓存在内存 |
| 复用 LLMProvider | 从现有 chat_service.py 迁移，保持多 Provider 支持 |

**Phase 1.0 验收标准**：选择角色 → 进入教室 → TeachingEngine 根据内置 YAML 选知识点 → ContextBudget 构建 Prompt → WS 流式返回 → 进度更新到 DB → 刷新后通过 state.sync 恢复。

### Phase 1.5 — 动态与个性

| 任务 | 说明 |
|------|------|
| EmotionEngine | 情感计算与衰减逻辑 (基于角色 YAML 的 emotion_profile) |
| EventEngine | 时间/条件/随机事件触发器 (基于 content/world/events.yaml) |
| WS 事件推送 | event.trigger + emotion.update + narrative.options |
| 用户上传教材 | 多格式解析器 + 状态机 (parsing → indexed → outlining → pending_review) |
| 人工确认前台 | Curriculum.vue 增加大纲审核页面 (确认/编辑/拒绝) |
| RAG 集成 | LlamaIndex + FAISS 最小实现 (长上下文模式作为 fallback) |
| 前端角色卡片 | Characters.vue 改造为动态情感展示 |
| 前端 Timeline.vue | 时间线可视化 |

### Phase 2.0 — 深化

| 任务 | 说明 |
|------|------|
| 完整课程内容 | ≥2 phase 的知识模块 YAML (含 teaching_hints) |
| AssessmentEngine | 考核模式 (测验/辩论赛) |
| 场景切换 UI | Scene.vue 场景描述 + 转场动画 |
| 大纲编辑器 | 用户可微调 LLM 生成的大纲 (拖拽排列知识点、修改依赖) |
| KnowledgeGraph 热重载 | 支持运行时重新加载 YAML |

### Phase 3.0 — 集成

| 任务 | 说明 |
|------|------|
| NarrativeEngine | 总调度引擎 (协调所有引擎) |
| 前端叙事管理器 | narrative.js Pinia store 完整实现 |
| 事件通知系统 | 事件弹窗 + 叙事选项 UI |
| 性能优化 | WS 消息压缩、ContextBudget tiktoken 精确计算 |

### Phase 4.0 — 打磨与发布

| 任务 | 说明 |
|------|------|
| 完善所有课程内容 | 90天完整大纲 |
| 性能优化 | WebSocket 连接管理、消息压缩 |
| 测试 | 单元测试 + 集成测试 + 叙事流程 E2E 测试 |
| Docker 部署更新 | 更新 docker-compose 适配新架构 |
| Windows 打包 | 更新 PyInstaller spec |

---

## 十四、可复用的现有代码

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

## 十五、关键设计决策

| 决策 | 选项 | 选择 | 理由 |
|------|------|------|------|
| 课程存储格式 | YAML 文件 vs 数据库表 | **YAML 文件** | 课程内容由设计者编写，非运行时频繁修改 |
| 知识依赖管理 | YAML 查询 vs 内存 DAG | **启动时加载 YAML 到内存 DAG** | 避免每次查询解析 YAML，支持拓扑排序和前置检查 |
| WebSocket 库 | `websockets` vs FastAPI 内置 | **FastAPI 内置** | 减少依赖，与现有框架统一 |
| 状态落盘 | 全写 DB vs 分级持久化 | **Critical 立即写 + Soft 定时批量** | 减少 DB 写入压力，区分可丢失和不可丢失状态 |
| 前端 Markdown 渲染 | marked + KaTeX vs MDX + React | **marked + KaTeX** | 已在 Chat.vue 中验证可行 |
| 多用户支持 | MVP 单用户 vs Phase 2 多用户 | **MVP 单用户** | 降低复杂度，状态模型 + user_id 即可扩展 |
| 大纲生成 | 全自动 vs 人工确认 | **LLM 生成 + 人工确认** | 防止幻觉依赖链导致教学混乱 |
| 大纲生成方式 | 同步 (用户等待) vs 异步 (即时可用) | **异步 + 降级可用** | 解析完即可自由对话，大纲后台生成后需人审 |
| Prompt 构建 | 简单拼接 vs Context Budget | **Context Budget 机制** | 防止 token 超限，确保关键上下文不被截断 |
| 知识图谱库 | networkx vs 自实现邻接表 | **MVP 用自实现邻接表** | 轻量无额外依赖，复杂分析需求再引入 networkx |
| RAG 方案 | FAISS (最小) vs RAGFlow (完整) | **FAISS MVP，Phase 1.0 先用长上下文** | 通过 BaseRAGProvider 抽象，可后续升级；Phase 1.0 无 RAG |
| WS 重连策略 | 无对账 vs state.sync 对账 | **重连后 state.sync 强制覆盖** | 防止断线期间增量推送丢失导致状态不一致 |