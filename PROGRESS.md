# 重构进度跟踪

> 基于 `docs/redesign_plan.md` v2 的叙事驱动架构重构。每完成一步即勾选并提交。

---

## Phase 1.0 — 核心循环 ✅

> Commit: `1736b1b8` | 状态：已完成并推送

- [x] 目录结构：`engines/`, `graph/`, `parsers/`, `state/`, `llm/`, `tasks/`
- [x] 内容 YAML：syllabus.yaml, 2 个模块 YAML, 3 个角色配置, 世界观设定
- [x] 6 个新 SQLAlchemy 模型：WorldState, CharacterState, LearningProgress, Syllabus, KnowledgePoint, EventLog
- [x] 更新 Material 模型（status, review_status, error_code 等）
- [x] 更新 Conversation 模型（knowledge_point_id, scene_id, narrative_context）
- [x] KnowledgeGraph：内存 DAG（邻接表），前置依赖检测，拓扑排序
- [x] ContextBudget：token 预算分配器，含 `<rule>` 场景约束
- [x] TeachingEngine：知识点选取 + prompt 构建使用 ContextBudget
- [x] WorldStateEngine：场景管理 + 时间推进 + YAML 配置加载
- [x] CharacterEngine：角色配置加载从 YAML
- [x] NarrativeEngine：最小协调器连接所有引擎
- [x] StateManager：Critical 立即写 + Soft 批量写
- [x] WebSocket handler（ws.py）：chat.send, scene.switch, state.sync
- [x] WS 协议 schemas（20+ 消息类型）
- [x] 4 个新 repositories + UoW 更新
- [x] 更新 enums.py（MaterialStatus, KnowledgePointStatus, EventType, ReviewStatus）
- [x] 更新 main.py（引擎初始化, StateManager 生命周期）
- [x] 前端：useWebSocket.js composable, narrative.js Pinia store, Curriculum.vue, Timeline.vue, router 更新

---

## Phase 1.5 — 情感与事件 ✅

> Commit: `27545fda` | 状态：已完成并推送

- [x] EmotionEngine：mood/trust 计算（含衰减）、角色敏感度曲线、表达生成
- [x] EventEngine：时间事件 / 条件事件 / 随机事件触发，从 YAML 加载，优先级评估
- [x] 文档解析器：PDF（pdfplumber + PyMuPDF fallback）、DOCX（python-docx）、TXT/MD（chardet 编码检测）、解析注册表（magic number + 扩展名派发）
- [x] Material pipeline：异步状态机（parsing → indexing → outlining → pending_review）、LLM 大纲生成、WS 通知
- [x] NarrativeEngine 更新：接收 emotion_engine / event_engine、情感 prompt 构建、事件触发场景切换
- [x] WS handler 更新：syllabus.confirm / reject, action.choose 消息类型
- [x] curriculum API：material status, syllabus review, module/point 查询
- [x] Chat.vue：WebSocket 替换 SSE 流式，处理 emotion.update / scene.change / event.trigger
- [x] Characters.vue：mood 标签显示（颜色编码）
- [x] RAG Service：FAISS 向量索引（MVP 哈希伪嵌入），分块检索，material pipeline 自动索引
- [x] requirements.txt 更新：faiss-cpu, numpy, pdfplumber, python-docx, chardet

---

## Phase 2.0 — 考核与场景 🔄

> 状态：未开始

- [ ] AssessmentEngine：quiz 生成、得分计算、掌握度判定
- [ ] NarrativeEngine 调用 AssessmentEngine 进行知识点考核
- [ ] 前端场景切换 UI（场景卡片、时间线可视化）
- [ ] 前端课程编辑器（查看/确认大纲、编辑知识点）
- [ ] RAG 嵌入升级：哈希伪嵌入 → 真实嵌入（sentence-transformers / OpenAI embeddings）
- [ ] 前端 Chat.vue 展示考核结果 + 进度条

---

## Phase 3.0 — 多学生协作 📋

> 状态：未开始

- [ ] 多用户系统（认证 / 授权）
- [ ] 学生学习分析仪表盘
- [ ] 教师 dashboard
- [ ] 对话历史搜索与管理增强

---

## Phase 4.0 — 插件与自定义 🔮

> 状态：未开始

- [ ] Plugin 系统
- [ ] 自定义世界观编辑器（前端 YAML 编辑器）
- [ ] 角色创建向导（支持自定义头像、人格模板）
- [ ] 国际化 i18n

---

## 已知问题 / 修复项

| 优先级 | 问题 | 状态 |
|--------|------|------|
| 🔴 高 | vite build 报错 @vitejs/plugin-vue resolve | 未修复 |
| 🟡 中 | RAG 使用哈希伪嵌入，检索精度有限 | Phase 2.0 升级 |
| 🟢 低 | EmotionEngine mood 判断基于关键词，未使用 LLM | 后续优化 |

---

## 关键架构决策记录

| 决策 | 选择 | 原因 |
|------|------|------|
| 静态内容格式 | YAML | 人类可写可读，git 友好 |
| 知识依赖 | 内存 DAG (邻接表) | MVP 够用，轻量 |
| Token 计数 | tiktoken cl100k_base | OpenAI 兼容 |
| WebSocket 实现 | FastAPI 内置 | 无额外依赖 |
| 状态持久化 | Critical 即时 + Soft 60s 批量 | 平衡性能与可靠性 |
| 大纲确认 | pending_review + 人工确认 | 质量保障 |
| RAG MVP | FAISS + 哈希伪嵌入 | 快速可用，Phase 2 升级 |
| 情感检测 | 关键词匹配 | MVP 够用，后续可加 LLM |