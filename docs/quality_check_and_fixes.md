# 教材管线质量校验与缺陷修复说明（2026-10-14）

## 1. 新增 quality_check 阶段

状态机由 `parsing → indexing → outlining → pending_review` 扩展为：

```
parsing → indexing → indexed → outlining → quality_check → pending_review
                                            └→ review_rejected（校验不通过）
```

- 校验器：`backend/app/tasks/quality_check.py` 的 `validate_outline(outline)`（纯函数，无 DB/LLM 依赖；别名 `check_outline_quality`）。
- 规则：
  1. **非空**：大纲为 dict，含非空 `name`，`modules` 为非空列表（`None` / 字符串等非法类型拒绝）；
  2. **知识点可解析**：每个知识点具备非空字符串 `id` / `name`，`id` 全局唯一；模块/知识点必须是对象；
  3. **数量门**：合法知识点数 ≥ `MIN_KNOWLEDGE_POINTS`（=1），空模块/空知识点列表拒绝；
  4. **前置依赖闭合**：`prerequisites` 必须是列表，引用的知识点必须已声明，不能自依赖，依赖图无环（DFS）。
- **防御性降级**：校验器自身抛异常时管线退回到 `indexed`（自由对话可用），而非整条 `failed`。
- 不通过：物料进入新状态 `review_rejected`（`MaterialStatus.REVIEW_REJECTED`），`review_status=rejected`，错误码记入 `error_code`，并通过现有通知机制发送两类事件：
  - `material.status_changed`（status=`review_rejected`）；
  - 新增专用事件 `material.quality_rejected`（payload 携带 `reasons` 列表与 `error_code`，schema 见 `ws_protocol.MaterialQualityRejectedEvent`）。
- 通过后才写 `syllabuses` 表并进入 `pending_review`；被拒绝的大纲不会落库。

枚举扩展（`backend/app/schemas/enums.py`）：
`MaterialStatus.QUALITY_CHECK`、`MaterialStatus.REVIEW_REJECTED`，以及 `QualityCheckErrorCode` 一组细粒度错误码。

## 2. 修复的真实缺陷（含根因与回归测试）

### F1. 文本直送路径 char_count 恒为 0
- **根因**：`ParseResult` 的 dataclass 默认 `char_count=0`；管线用 `getattr(result, 'char_count', len(result.text))` 取长度，`getattr` 的默认值只在**属性缺失**时生效，属性存在（值为 0）时直接返回 0，于是物料表 `char_count` 被写成 0，前端字数统计失真。
- **修复**：构造文本路径 `ParseResult` 时写入 `char_count=len(text)`；索引落库时用 `getattr(result, 'char_count', 0) or len(result.text)` 兜底。
- **回归测试**：`TestPipelineHappyPaths::test_text_path_full_flow_to_pending_review` 断言 `char_count == len(content)`。

### F2. pending_review 更新作用在 detached 对象上
- **根因**：大纲阶段沿用索引阶段已关闭会话里取出的 `material` 对象，在新会话里对其 `update`，ORM 会话已分离，状态写入可能不落库。
- **修复**：在 `pending_review` 的会话内重新 `get_by_id`，再更新并创建 syllabus；物料不存在时显式抛错进入 `failed`。
- **回归测试**：端到端 happy-path 从 DB 重新 refresh 断言 `status=pending_review` 且 syllabus 已创建。

### F3. 索引阶段物料缺失被静默跳过
- **根因**：索引阶段 `if material:` 为假时仅跳过更新，流程继续走向大纲生成，最终产生无主大纲。
- **修复**：物料不存在时抛 `MaterialPipelineError(MATERIAL_NOT_FOUND)`，由顶层兜底进入 `failed`。
- **回归测试**：`TestPipelineIndexAndOutlineFailures::test_missing_material_at_index_phase_ends_failed`。

### F4. EmotionEngine 对 YAML 引号敏感度值崩溃
- **根因**：角色 YAML 中 `event_sensitivity` 常被写成 `"+0.08"`（字符串），`current_mood + delta` 触发 `TypeError: unsupported operand`；`trust_growth_rate/max_trust/base_mood` 同样可能被引号包住。
- **修复**：新增 `_coerce_delta()`，把字符串（含 `+` 号）安全转 float，失败回退到调用方传入的默认值；`update / apply_decay / 初始化 / trust` 全部走该转换。
- **回归测试**：`TestEmotionEngine::test_string_quoted_sensitivity_coerced`（字符串 `+0.08` 更新与衰减均正常）。

### F5. `handle_assessment_answer` 的死查询与载荷形态崩溃
- **根因**：①函数内先执行一条全表 COUNT 的 `SELECT count(*)` 但结果从未使用（死代码，徒增 DB 压力）；②`for q, a in answers:` 直接元组解包，前端若传 `{"question": ..., "answer": ...}` 的 dict 列表会直接 `ValueError: cannot unpack`。
- **修复**：删除死查询；新增 `_normalize_answer_entry()` 同时兼容 `[question, answer]` 对与 `{question, answer}` dict，畸形条目跳过而非中断考核。
- **回归测试**：`test_handle_assessment_answer_dict_payload_no_crash`、`test_handle_assessment_answer_tuple_payload_still_supported`。

### F6. repair-stuck 对无内容卡死物料无解
- **根因**：原端点只重处理 `material.content` 非空的卡死物料；`parsing` 状态且无文件无内容的物料永远挂起，无法自愈。
- **修复**：抽出可注入的 `repair_stuck_materials(uow_factory, ws_notify, reprocess, schedule)`：有内容→按文本路径重新入队（默认 `asyncio.create_task`，可替换调度器便于测试）；无内容→标记 `failed`（`error_code=STUCK_NO_CONTENT`）；返回 `{repaired, failed, stuck}` 清单。REST 端点 `/materials/repair-stuck` 改调该函数，响应保持向后兼容（`repaired` 列表）并附带 `failed`。
- **回归测试**：`TestRepairStuck::test_repair_stuck_marks_contentless_material_failed`、`test_repair_stuck_requeues_material_with_content`、混合队列、空队列；e2e `tests/e2e/test_repair_stuck_api.py` 覆盖 REST。

### F7. 重复触发堆积多条 syllabus（第二轮发现并修复）
- **根因**：`pending_review` 阶段无条件 `syllabuses.create()`；手动重跑或 repair-stuck 再次入队同一物料时会插入多行，而 `SyllabusRepository.get_by_material_id` 使用 `scalar_one_or_none`，命中多行即报错。
- **修复**：进入 pending_review 时先查已有 syllabus，存在则 `update`，否则 `create`，保证幂等。
- **回归测试**：`TestDuplicateAndConcurrent::test_duplicate_trigger_converges_to_pending_review` 断言重复触发后仅 1 条 syllabus；`test_concurrent_triggers_both_finish_and_converge` 用 `asyncio.gather` 双触发，收敛到 `pending_review` 且无未捕获异常。

## 3. 测试分布（全部内存 SQLite / mock LLM，无外部服务）

| 文件 | 覆盖 |
| --- | --- |
| `tests/unit/test_quality_check.py` | 校验器全部规则：空大纲、缺模块、缺 id/name、重复 id、未声明前置、自依赖、循环依赖、类型错误、合法链；modules 为 None/字符串/非法条目、空模块阈值边界、`check_outline_quality` 别名 |
| `tests/unit/test_material_pipeline.py` | 文本/真实文件 happy path（含 source×outline 参数化矩阵）；文件缺失、解析失败（错误码透传）、索引阶段物料丢失/DB 异常、大纲异常/空响应回退 indexed、质量拒绝不落 syllabus、校验器内部异常降级 indexed、RAG 故障非致命、WS 通知抛错不崩；repair-stuck 三态；`_generate_outline` 的 fenced JSON / think-tag 清洗 / 空响应 / 非法 JSON / 无模型配置 |
| `tests/unit/test_pipeline_regressions.py` | F1–F6 每个缺陷一条真实内存 SQLite 端到端回归，断言修复前后行为差异 |
| `tests/unit/test_pipeline_state_machine.py` | quality_check→pending_review / →review_rejected 完整事件序列、能力标记、重复触发幂等、并发触发收敛 |
| `tests/unit/test_engines.py` | AssessmentEngine 掌握度判定（高分通过、低分学习、尝试惩罚、review_needed、空分、上下限、选择/开放题评分、触发规则、quiz 边界）；EmotionEngine（初始化、correct/wrong、未知角色、mood 封顶、字符串敏感度、衰减时长与地板）；NarrativeEngine（自由对话/结构化 prompt 组装、情感关键词路由、mood 描述阈值、测验启停与评分、mock LLM 出题、流式编排落库与 emotion 事件、考核答案兼容载荷） |
| `tests/e2e/test_repair_stuck_api.py` | REST repair-stuck 空队列/无内容失败/有内容入队 |
| `tests/e2e/test_material_api_boundary.py` | 教材创建空标题/超长标题 422、长度边界、404；confirm/reject-syllabus 状态守卫 400/404、pending_review 确认成功；WS ping/pong、非法 JSON、缺字段、未知类型 |

## 4. 未破坏的既有行为

- 原有 92 个测试全部保持通过；两轮新增后共 **219 passed, 5 skipped**（skip 为原有的 faiss/sentence-transformers 环境探测；1–2 条 aiosqlite 线程在事件循环关闭时的 PytestUnhandledThreadExceptionWarning 为环境既有噪音，不影响结果）。
- REST/WS 既有事件名（`material.status_changed`、`chat.token`、`chat.complete`、`emotion.update`、`assessment.*` 等）与载荷结构未改，仅新增 `material.quality_rejected` 事件与 `review_rejected` 状态；`curriculum.py` 的 `free_chat` 能力集合把新状态纳入，不影响旧状态判定。
