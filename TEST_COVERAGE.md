# Test Coverage Analysis

> Generated: 2026-06-09 after full codebase review + fixes

## Quick Status

```
tests/unit/test_schemas.py             21 ✓   (最佳)
tests/unit/test_rag_service.py         14 ✓
tests/unit/test_repositories.py        11 ✓
tests/unit/test_assessment_engine.py    9 ✓
tests/unit/test_narrative_assessment.py 5 ✓
tests/e2e/test_api_e2e.py             24 ✓  3 ✗
────────────────────────────────────────────
Total: 94 passed · 4 errors · 0 failed
```

4 errors: 3 need `pip install pytest-mock`, 1 is a fire-and-forget task race at teardown.

## Frontend Coverage: 0%

- No test runner configured (`package.json` has no `"test"` script)
- No `vitest`, `jest`, or any component test framework
- Phase 3 extracted components (`MessageBubble`, `TypingIndicator`, `ChatMessages`, `MarkdownContent`, `ChatInput`, `ChatHeader`, `ChatSidebar`) — zero tests
- Composable (`useWebSocket`, `useCharacterAvatar`) — zero tests
- Store (`narrative.js`, `character.js`, `conversation.js`) — zero tests
- Views (15 files) — zero tests

## Backend Coverage Gaps

### Core logic — no tests at all
| Module | Risk |
|---|---|
| `engines/teaching_engine` | Hint generation logic untested |
| `engines/emotion_engine` | Mood/trust update logic untested |
| `engines/event_engine` | Event triggering untested |
| `engines/world_state_engine` | World state transitions untested |
| `engines/ui_orchestrator` | LLM→UI mapping untested |
| `graph/knowledge_graph` | Two-pass prereq resolution (new) untested |
| `llm/context_budget` | Token budget calculation untested |
| `core/*` | Config, DB init, rate limiter — untested |
| `parsers/*` | PDF/DOCX/TXT parsing — untested |
| `tasks/material_pipeline` | Background pipeline — untested (fires during E2E, causes teardown crash) |

### API — missing endpoints in E2E
- `api/v1/upload.py` — upload/avatar, upload/background, all background CRUD
- `api/v1/ws.py` — WebSocket is the core real-time channel, completely untested
- `api/v1/curriculum.py` — syllabus generation, outline, module listing
- `api/v1/chat.py` stream endpoint — E2E test exists but mock depends on `pytest-mock`

### Repository — incomplete unit tests
- `MaterialRepository`: missing update, delete, not-found tests
- `MessageRepository`: missing update, delete, empty conversation tests
- `ConversationRepository`: missing update, delete tests
- All other repositories (7 more): no unit tests at all

## Blockers

1. **`pytest-mock` not installed** — 3 E2E tests error on `mocker` fixture
2. **`asyncio.create_task` race** — `material_pipeline.process_material` outlives test DB engine; needs to be mocked in E2E tests
3. **WebSocket testing** — requires `websockets` library for `connect()`/`disconnect()` simulation

## Priority Fixes

1. `pip install pytest-mock` → +3 passing tests immediately
2. Add `vitest` + `@vue/test-utils` to frontend → Phase 3 component tests
3. `KnowledgeGraph` unit tests → critical after two-pass refactor
4. Mock `process_material` in E2E tests → stabilize teardown
5. WebSocket E2E tests → core real-time flow
