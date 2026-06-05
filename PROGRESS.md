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

## Phase 2.0 — 考核与场景 🔧

> 状态：已完成

- [x] AssessmentEngine：quiz 生成 (LLM prompt)、答案评分、掌握度计算、状态判定
- [x] NarrativeEngine 集成 AssessmentEngine：自动触发考核 (should_trigger_assessment)、考核答案处理、掌握度持久化
- [x] WS 新增 assessment.generate / assessment.answer 消息类型
- [x] WS event: assessment.start / assessment.quiz / assessment.result
- [x] 前端 Chat.vue：考核面板 UI (选择题+简答题)、考核结果展示、掌握度进度条
- [x] Narrative store：currentAssessment / assessmentResult 状态管理
- [x] useWebSocket.js：generateAssessment / submitAssessment / advanceTime 方法
- [x] REST API：POST /assessment/generate、GET /progress/{point_id}
- [x] 前端场景切换 UI：Timeline.vue 重构，场景卡片点击切换，时间推进按钮，WS time.advance
- [x] 前端课程编辑器：Curriculum.vue 重构，知识点进度+掌握度、阶段折叠、一键测验按钮、同步按钮
- [x] RAG 嵌入升级：支持 sentence-transformers / OpenAI / hash 三级 fallback

---

## Phase 3.0 — 单用户体验优化 ✅

> 状态：已完成（从多用户认证改为单用户桌面应用）

- [x] 学习进度 Dashboard：GET /curriculum/progress-summary（无认证）
- [x] Dashboard.vue：学习统计卡片 + 知识点掌握度表格
- [x] Home.vue：学习中心入口
- [x] ~~JWT 认证系统~~ （已移除，单人桌面应用无需认证）
- [x] ~~User 模型 / Login.vue / useUserStore / 路由守卫~~ （已移除）
- [x] ~~Teacher Dashboard~~ （已移除，教师是虚拟角色非真实用户）

---

## Phase 4.0 — 打磨与增强 ✅

> 状态：已完成

- [x] 对话历史搜索与管理增强
  - 后端: ConversationRepository.search() 支持关键词+角色ID搜索、MessageSearchRepository 全文搜索
  - 后端: /content/conversations/search, /content/conversations/{id}/messages/search, /content/conversations/stats API
  - 前端: Conversations.vue 重构 — 搜索栏、角色筛选、分页、统计栏、近7天计数
  - 前端: api/index.js 新增 conversations.search, conversations.stats, content.* 系列 API
- [x] 世界观 YAML 编辑器
  - 后端: /content/yaml/list, /content/yaml/{path} (GET/PUT) — 读取/保存 YAML 内容，自动备份，YAML 语法校验
  - 前端: YamlEditor.vue — 文件列表+YAML源码编辑器+结构预览 (YamlPreview.vue 递归组件)
  - 前端: js-yaml 客户端解析预览
- [x] 角色创建向导
  - 后端: /content/characters/create — 从模板创建角色 YAML 文件，自动加载到 CharacterEngine
  - 后端: /content/characters/templates — 4 个内置模板 (苏格拉底式/实践型/学术型/故事型)
  - 前端: CharacterCreator.vue — 4步向导 (选模板→基本信息→提示&情感→确认)
- [x] 世界观/角色热重载
  - 后端: POST /content/reload — 热重载 KnowledgeGraph, CharacterEngine, WorldStateEngine, EmotionEngine, EventEngine
  - 前端: YamlEditor.vue 中"热重载"按钮
  - WorldStateEngine.reload(), EmotionEngine.reload(), EventEngine.reload() 方法
- [x] 事件通知弹窗 + 叙事选项 UI
  - 后端: EventEngine 事件定义增加 options 字段，TriggeredEvent 携带选项数据
  - 后端: NarrativeEngine 发送 narrative.options WS 事件（含选项列表）
  - 前端: Chat.vue 事件通知弹窗组件（含动画过渡）
  - 前端: 叙事选项按钮 UI，用户选择后发送 action.choose WS 消息
  - 前端: 监听 narrative.options / event.trigger / event.resolved 事件
- [x] 大纲编辑器（拖拽排列知识点、修改依赖）
  - 前端: Curriculum.vue 新增"编辑"视图模式
  - 拖拽排序知识点（HTML5 Drag & Drop API）
  - 修改知识点名称、难度、核心概念
  - 添加/移除前置依赖关系
  - 保存修改通过 YAML 编辑 API 写入文件并触发热重载
- [x] NarrativeEngine 使用 ContextBudget
  - handle_chat_message 改为使用 TeachingEngine.build_teaching_prompt()（含 ContextBudget）
  - 结构化模式下完整利用 ContextBudget 的 token 预算分配、<rule> 场景约束
  - 非结构化模式保留简化 prompt 构建
  - RAG 上下文、情感摘要注入到 prompt 构建流程
  - 直接使用 LLMProvider.chat_stream 替代 ChatService.chat_stream
- [⏭] ~~国际化 i18n~~ — 单用户桌面应用、中文目标用户，暂不做

---

---

## 打包待办

| 项 | 说明 | 状态 |
|----|------|------|
| main.spec hiddenimports | 缺少 faiss-cpu, sentence_transformers, pdfplumber, python_docx, chardet, tiktoken, slowapi, limits | 重构完成后统一更新 |
| main.spec datas | 缺少 content/ 目录（YAML 内容文件） | 重构完成后统一更新 |
| python-jose, bcrypt, passlib | 已移除（单用户无需认证），需从 spec 中确认删除 | 重构完成后统一更新 |
| requirements-prod.txt | Docker 用，需与 requirements.txt 同步 | 重构完成后统一更新 |
| npm install | 用户开发时需手动执行，打包脚本已有 npm run build 步骤 | 已有 |

| 优先级 | 问题 | 状态 |
|--------|------|------|
| 🔴 高 | vite build 报错 @vitejs/plugin-vue resolve | ✅ 已修复（node_modules 重装） |
| 🟡 中 | RAG 使用哈希伪嵌入，检索精度有限 | ✅ Phase 2.0 升级为三级 fallback |
| 🟡 中 | EventEngine 缺少优先级评估 | ❌ 事件按 YAML 加载顺序返回，无 priority 字段和排序逻辑 |
| 🟡 中 | PDF fallback 库名错误 | ❌ PROGRESS 写 PyMuPDF，实际代码用 PyPDF2 |
| 🟡 中 | Material pipeline 卡在 parsing 状态 | ✅ 已修复：process_material 从未被调用+repair-stuck 端点 |
| 🟡 中 | 历史对话加载缺失 | ✅ 已修复：loadConversation 未赋值 messages |
| 🟡 中 | RAG 未接入 REST 聊天路径 | ✅ 已修复：ChatService._build_messages 优先 RAG 检索 |
| 🟡 中 | 后端启动卡住 30s+ | ✅ 已修复：FAISS/numpy/fastembed 懒加载 |
| 🟢 低 | EmotionEngine mood 判断基于关键词，未使用 LLM | 后续优化 |
| 🟢 低 | 考核掌握度进度条 | ⚠️ Chat.vue 显示为文字 XX%，非可视进度条组件（Dashboard 有 progress bar） |
| 🟢 低 | WS 协议 schema 数量 | ⚠️ PROGRESS 写 20+，实际 Pydantic schema 14 个（含服务端推送共 27 种消息类型） |

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
| RAG MVP | FAISS + 三级嵌入 fallback | sentence-transformers 优先，hash 保底 |
| Route 修复 | /curriculum/curriculum → /curriculum | 去除重复前缀 |
| 情感检测 | 关键词匹配 | MVP 够用，后续可加 LLM |
| 对话搜索 | SQLAlchemy ilike + 子查询 | 标题/内容双维度搜索 |
| YAML 编辑 | API 读写 + 自动备份 | 保存前 YAML 语法校验，.bak 回滚 |
| 角色创建 | YAML 模板 + 向导 UI | 4 模板，创建后自动热加载到引擎 |
| 热重载 | POST /content/reload | 不重启进程重新加载所有 YAML 内容到内存 |
| 事件通知 | WS narrative.options + 弹窗 UI | 事件触发时推送选项，用户选择后发送 action.choose |
| 大纲编辑 | 拖拽排序 + 依赖编辑 | HTML5 Drag & Drop，保存通过 YAML API + 热重载 |
| ContextBudget 集成 | TeachingEngine.build_teaching_prompt | 结构化模式走 ContextBudget，非结构化走简化 prompt |
| 教材-大纲-时间线绑定 | syllabus.activate | 一个教材=一个学习旅程，切换教材重载KG+时间线 |
| 默认学习周期 | 15天（原90天） | settings.yaml base_days + syllabus.yaml total_days |