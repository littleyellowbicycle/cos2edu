# Phase 2.0 — 考核与场景 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement AssessmentEngine for quizzes/scoring/mastery, integrate it with NarrativeEngine, add Scene/Exam UI views, build curriculum editor for syllabus review, and upgrade RAG from hash-pseudo to sentence-transformers embeddings.

**Architecture:** AssessmentEngine integrates as a new engine called by NarrativeEngine when scene is `exam_room`. Scene.vue and Exam.vue are new Vue views added to the router. Curriculum.vue gets a syllabus review panel. RAG gets a real embedding provider alongside the existing hash fallback.

**Tech Stack:** Python/FastAPI backend, Vue 3 + Element Plus frontend, sentence-transformers for embeddings, pytest for tests

---

## Task 1: AssessmentEngine — Quiz Generation & Scoring

**Files:**
- Create: `backend/app/engines/assessment_engine.py`
- Create: `tests/unit/test_assessment_engine.py`
- Modify: `backend/app/engines/__init__.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_assessment_engine.py
import pytest
from app.engines.assessment_engine import AssessmentEngine, QuizQuestion, QuizResult

class TestAssessmentEngine:
    def setup_method(self):
        self.engine = AssessmentEngine()

    def test_generate_quiz_from_knowledge_point(self):
        point = {
            "id": "perceptron",
            "name": "感知机",
            "difficulty": 2,
            "key_concepts": ["线性分类", "激活函数", "损失函数"],
            "suggested_questions": ["如果数据不是线性可分的，感知机会发生什么？"],
        }
        quiz = self.engine.generate_quiz(point, num_questions=3)
        assert len(quiz.questions) <= 3
        assert quiz.knowledge_point_id == "perceptron"
        assert quiz.difficulty == 2

    def test_score_quiz_result(self):
        result = self.engine.score_quiz(
            knowledge_point_id="perceptron",
            total_questions=4,
            correct_answers=3,
        )
        assert result.mastery_level > 0.5
        assert result.knowledge_point_id == "perceptron"
        assert result.passed is True

    def test_score_quiz_fail(self):
        result = self.engine.score_quiz(
            knowledge_point_id="perceptron",
            total_questions=4,
            correct_answers=1,
        )
        assert result.mastery_level < 0.5
        assert result.passed is False

    def test_determine_mastery_from_repeated_attempts(self):
        # First attempt: barely pass
        r1 = self.engine.score_quiz("perceptron", 4, 3)
        assert r1.mastery_level == 0.75
        # Second attempt with perfect score should increase mastery
        r2 = self.engine.score_quiz("perceptron", 4, 4, previous_attempts=1)
        assert r2.mastery_level > r1.mastery_level
```

**Step 2: Run test to verify it fails**

Run: `cd D:\project\cos2edu\cos2edu && python -m pytest tests/unit/test_assessment_engine.py -v`
Expected: FAIL (module not found)

**Step 3: Write AssessmentEngine implementation**

```python
# backend/app/engines/assessment_engine.py
from dataclasses import dataclass, field
from typing import Optional
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class QuizQuestion:
    question_text: str
    options: list[str]
    correct_answer: int  # index into options
    difficulty: int = 1


@dataclass
class Quiz:
    knowledge_point_id: str
    knowledge_point_name: str
    difficulty: int
    questions: list[QuizQuestion] = field(default_factory=list)


@dataclass
class QuizResult:
    knowledge_point_id: str
    mastery_level: float
    correct_count: int
    total_questions: int
    passed: bool
    feedback: str = ""


class AssessmentEngine:
    PASSING_THRESHOLD = 0.6

    def generate_quiz(
        self,
        knowledge_point: dict,
        num_questions: int = 4,
    ) -> Quiz:
        point_id = knowledge_point.get("id", "unknown")
        point_name = knowledge_point.get("name", "Unknown")
        difficulty = knowledge_point.get("difficulty", 1)
        key_concepts = knowledge_point.get("key_concepts", [])
        suggested = knowledge_point.get("suggested_questions", [])

        questions = []

        if suggested:
            for sq in suggested[:num_questions]:
                options = self._generate_options(sq, key_concepts)
                questions.append(QuizQuestion(
                    question_text=sq,
                    options=options,
                    correct_answer=0,
                    difficulty=difficulty,
                ))

        while len(questions) < num_questions and key_concepts:
            concept = key_concepts[len(questions) % len(key_concepts)]
            question_text = f"关于「{concept}」，以下哪个说法是正确的？"
            options = self._generate_concept_options(concept, key_concepts)
            questions.append(QuizQuestion(
                question_text=question_text,
                options=options,
                correct_answer=0,
                difficulty=difficulty,
            ))

        return Quiz(
            knowledge_point_id=point_id,
            knowledge_point_name=point_name,
            difficulty=difficulty,
            questions=questions[:num_questions],
        )

    def score_quiz(
        self,
        knowledge_point_id: str,
        total_questions: int,
        correct_answers: int,
        previous_attempts: int = 0,
    ) -> QuizResult:
        base_mastery = correct_answers / total_questions if total_questions > 0 else 0

        attempt_bonus = min(0.1, previous_attempts * 0.05) if base_mastery >= self.PASSING_THRESHOLD else 0
        mastery_level = min(1.0, base_mastery + attempt_bonus)

        passed = mastery_level >= self.PASSING_THRESHOLD and correct_answers >= total_questions * 0.5

        if passed:
            if mastery_level >= 0.9:
                feedback = "优秀！你已经完全掌握了这个知识点。"
            elif mastery_level >= 0.7:
                feedback = "不错！你对这个知识点的理解较好，可以继续深入。"
            else:
                feedback = "及格了，但还需要加强练习来巩固理解。"
        else:
            feedback = "还需要再努力一下。建议回顾相关概念后再次尝试。"

        return QuizResult(
            knowledge_point_id=knowledge_point_id,
            mastery_level=round(mastery_level, 2),
            correct_count=correct_answers,
            total_questions=total_questions,
            passed=passed,
            feedback=feedback,
        )

    def _generate_options(self, question: str, key_concepts: list[str]) -> list[str]:
        return [
            "上述说法是正确的",
            "上述说法是错误的",
            "部分正确，但需要更多条件",
            "无法确定",
        ]

    def _generate_concept_options(self, concept: str, all_concepts: list[str]) -> list[str]:
        other = [c for c in all_concepts if c != concept]
        return [
            f"{concept}是核心概念",
            f"{other[0] if other else '其他概念'}更重要" if other else "这个概念不重要",
            f"{concept}只在特定条件下适用",
            "以上都不对",
        ]
```

**Step 4: Update `backend/app/engines/__init__.py`**

Add `AssessmentEngine`, `EmotionEngine`, `EventEngine` to exports:

```python
from .world_state_engine import WorldStateEngine
from .character_engine import CharacterEngine
from .teaching_engine import TeachingEngine
from .narrative_engine import NarrativeEngine
from .emotion_engine import EmotionEngine
from .event_engine import EventEngine
from .assessment_engine import AssessmentEngine

__all__ = [
    "WorldStateEngine",
    "CharacterEngine",
    "TeachingEngine",
    "NarrativeEngine",
    "EmotionEngine",
    "EventEngine",
    "AssessmentEngine",
]
```

**Step 5: Run tests**

Run: `cd D:\project\cos2edu\cos2edu && python -m pytest tests/unit/test_assessment_engine.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/engines/assessment_engine.py backend/app/engines/__init__.py tests/unit/test_assessment_engine.py
git commit -m "feat: add AssessmentEngine for quiz generation and mastery scoring"
```

---

## Task 2: Integrate AssessmentEngine into NarrativeEngine

**Files:**
- Modify: `backend/app/engines/narrative_engine.py`
- Create: `backend/app/schemas/ws_protocol.py` (add assessment message types)
- Create: `tests/unit/test_narrative_assessment.py`

**Step 1: Add assessment message types to ws_protocol.py**

Add these new types after the existing message classes:

```python
class SyllabusRejectMessage(WSMessage):
    type: str = "syllabus.reject"
    payload: dict = {}

class AssessmentRequestMessage(WSMessage):
    type: str = "assessment.start"
    payload: dict = {}  # {"knowledge_point_id": "perceptron"}

class AssessmentAnswerMessage(WSMessage):
    type: str = "assessment.answer"
    payload: dict = {}  # {"question_index": 0, "answer_index": 2}

class AssessmentResultEvent(WSMessage):
    type: str = "assessment.result"
    payload: dict = {}
```

**Step 2: Add assessment handling to NarrativeEngine**

Add `AssessmentEngine` as an optional dependency to `NarrativeEngine.__init__()`, and add an `handle_assessment` method that:
1. Receives a knowledge_point_id
2. Fetches the point metadata from KnowledgeGraph
3. Uses AssessmentEngine to generate a quiz
4. Returns quiz questions via WS
5. On assessment.answer, scores the quiz and emits progress.update

Add to `NarrativeEngine`:
- New method `start_assessment(knowledge_point_id: str) -> dict`
- New method `submit_assessment_answer(knowledge_point_id: str, answers: list[int]) -> dict`

The `start_assessment` method generates quiz questions and returns them. The `submit_assessment_answer` method scores and triggers a `progress.update` WS event.

**Step 3: Update ws.py to handle assessment messages**

Add handlers for `assessment.start` and `assessment.answer` message types that delegate to NarrativeEngine.

**Step 4: Write tests**

Test that `NarrativeEngine.start_assessment()` returns a quiz, and `NarrativeEngine.submit_assessment_answer()` returns a QuizResult and triggers state update.

**Step 5: Run tests and commit**

```bash
git commit -m "feat: integrate AssessmentEngine into NarrativeEngine with WS protocol"
```

---

## Task 3: Frontend Scene.vue — Scene Switching UI

**Files:**
- Create: `frontend/src/views/Scene.vue`
- Modify: `frontend/src/router/index.js`

**Step 1: Create Scene.vue**

Scene.vue should:
- Display current scene info (name, description, allowed actions) from `useNarrativeStore().world.currentScene`
- Show scene transition animations (CSS transitions)
- Provide action buttons mapped to `allowed_actions` (teach, question, discuss, debate, present, vote, exam, review)
- Listen for `scene.change` WS events and update the narrative store
- Include a `switchScene()` method that sends `scene.switch` via WebSocket

Template structure:
```vue
<template>
  <div class="scene-container" :class="sceneClass">
    <div class="scene-header">
      <h2>{{ currentScene.name }}</h2>
      <p class="scene-desc">{{ currentScene.description }}</p>
    </div>
    <div class="scene-actions">
      <el-button v-for="action in allowedActions" :key="action"
        @click="performAction(action)">
        {{ actionLabels[action] }}
      </el-button>
    </div>
  </div>
</template>
```

**Step 2: Add `/scene` route to router**

```javascript
{ path: '/scene', name: 'Scene', component: () => import('../views/Scene.vue') }
```

**Step 3: Add navigation to Scene.vue from Home.vue or Chat.vue**

Add a "场景" nav item or make scene transitions automatic via narrative store reactivity.

**Step 4: Commit**

```bash
git commit -m "feat: add Scene.vue with scene switching and action buttons"
```

---

## Task 4: Frontend Exam.vue — Assessment/Quiz Interface

**Files:**
- Create: `frontend/src/views/Exam.vue`
- Modify: `frontend/src/router/index.js`

**Step 1: Create Exam.vue**

Exam.vue should:
- Display quiz questions one at a time
- Show progress bar (question X of Y)
- Submit answers via `assessment.answer` WS message
- Show results with mastery level and feedback
- Trigger `progress.update` animation on completion
- Allow retry if failed

Template structure:
```vue
<template>
  <div class="exam-container">
    <div v-if="!quizStarted" class="exam-intro">
      <h2>📝 知识点考核</h2>
      <p>知识点: {{ knowledgePointName }}</p>
      <p>难度: {{ '⭐'.repeat(difficulty) }}</p>
      <el-button type="primary" @click="startAssessment">开始考核</el-button>
    </div>
    <div v-else-if="!quizFinished" class="exam-questions">
      <el-progress :percentage="progressPercentage" />
      <div class="question-card">
        <h3>{{ currentQuestion.question_text }}</h3>
        <el-radio-group v-model="selectedAnswer">
          <el-radio v-for="(option, i) in currentQuestion.options" :key="i"
            :value="i">{{ option }}</el-radio>
        </el-radio-group>
      </div>
      <el-button @click="nextQuestion" :disabled="selectedAnswer === null">
        {{ isLastQuestion ? '提交答案' : '下一题' }}
      </el-radio-button>
    </div>
    <div v-else class="exam-results">
      <el-result :icon="resultIcon" :title="resultTitle" :sub-title="resultFeedback">
        <template #extra>
          <p>掌握度: {{ (result.mastery_level * 100).toFixed(0) }}%</p>
          <p>正确: {{ result.correct_count }}/{{ result.total_questions }}</p>
          <el-button v-if="!result.passed" @click="retryAssessment">重新考核</el-button>
          <el-button type="primary" @click="goBack">返回学习</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>
```

**Step 2: Add `/exam` route**

```javascript
{ path: '/exam', name: 'Exam', component: () => import('../views/Exam.vue') }
```

**Step 3: Commit**

```bash
git commit -m "feat: add Exam.vue with quiz interface and mastery display"
```

---

## Task 5: Curriculum Editor — Syllabus Review & Edit

**Files:**
- Modify: `frontend/src/views/Curriculum.vue`
- Add syllabus review panel (confirm/reject/edit)

**Step 1: Add review panel to Curriculum.vue**

Add a review section that:
- Shows when a material has `pending_review` status
- Displays the generated syllabus outline
- Provides three buttons: 确认 (confirm), 编辑 (edit), 放弃 (reject)
- For edit: allows reordering knowledge points and modifying difficulty
- Calls `syllabus.confirm` or `syllabus.reject` via WS or REST API

**Step 2: Add material status column**

Show status badges (parsing, indexing, outlining, pending_review, ready, failed) next to each material.

**Step 3: Commit**

```bash
git commit -m "feat: add syllabus review panel to Curriculum.vue"
```

---

## Task 6: Frontend Chat.vue — Assessment Results + Progress Bar

**Files:**
- Modify: `frontend/src/views/Chat.vue`
- Add progress.update handler in useWebSocket

**Step 1: Add assessment result rendering in Chat.vue**

When a `progress.update` event arrives:
- Show a toast notification with the mastery change
- Update the progress bar in the sidebar/hydroecraft

When an `assessment.result` event arrives:
- Show a modal/inline card with quiz results
- Display mastery level as a progress bar with percentage

**Step 2: Add progress bar component**

A small reusable `<MasteryBar>` component that shows:
- Knowledge point name
- Mastery percentage (0-100%)
- Color coding (red < 60%, yellow < 80%, green >= 80%)

**Step 3: Commit**

```bash
git commit -m "feat: add assessment result display and mastery progress bar to Chat.vue"
```

---

## Task 7: RAG Embedding Upgrade — sentence-transformers

**Files:**
- Modify: `backend/app/services/rag_service.py`
- Create: `backend/app/rag/__init__.py`
- Create: `backend/app/rag/base.py`
- Create: `backend/app/rag/simple_rag.py`
- Modify: `backend/app/core/config.py` (add RAG_PROVIDER setting)
- Create: `tests/unit/test_rag_service.py`

**Step 1: Create RAG abstraction layer**

```python
# backend/app/rag/base.py
from abc import ABC, abstractmethod
from typing import List, Dict

class BaseRAGProvider(ABC):
    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        pass

    @abstractmethod
    async def add_documents(self, documents: List[Dict]) -> bool:
        pass

    @abstractmethod
    async def delete_documents(self, doc_ids: List[str]) -> bool:
        pass
```

**Step 2: Create SimpleRAGProvider (sentence-transformers)**

```python
# backend/app/rag/simple_rag.py
class SimpleRAGProvider(BaseRAGProvider):
    def __init__(self):
        self._model = None  # Lazy load sentence-transformers
        self._index = None   # FAISS index
        self._documents = []
        self._embeddings_dim = 384  # all-MiniLM-L6-v2 default

    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        if not self._index or not self._documents:
            return []
        query_embedding = self._embed(query)
        scores, indices = self._index.search(query_embedding, min(top_k, len(self._documents)))
        return [
            {"content": self._documents[i]["content"], "score": float(scores[0][j]), "metadata": self._documents[i].get("metadata", {})}
            for j, i in enumerate(indices[0]) if i >= 0
        ]

    async def add_documents(self, documents: List[Dict]) -> bool:
        # Embed and add to FAISS index
        ...

    async def delete_documents(self, doc_ids: List[str]) -> bool:
        # Rebuild index without specified docs
        ...
```

**Step 3: Add RAG_PROVIDER config**

In `config.py`, add:
```python
RAG_PROVIDER: str = "simple"  # "simple" | "ragflow"
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
VECTOR_DB_PATH: str = "./data/vectors"
```

**Step 4: Create RAG factory**

```python
# backend/app/rag/__init__.py
from app.rag.base import BaseRAGProvider
from app.rag.simple_rag import SimpleRAGProvider

def get_rag_provider(provider: str = None) -> BaseRAGProvider:
    if provider is None:
        from app.core.config import settings
        provider = settings.RAG_PROVIDER
    if provider == "simple":
        return SimpleRAGProvider()
    raise ValueError(f"Unknown RAG provider: {provider}")
```

**Step 5: Update rag_service.py to use the provider**

Refactor the existing `rag_service.py` to delegate to `SimpleRAGProvider` instead of its inline hash-based embedding.

**Step 6: Install dependencies**

Add to `requirements-prod.txt`:
```
sentence-transformers>=2.2.0
faiss-cpu>=1.7.4
```

**Step 7: Write tests**

Test that `SimpleRAGProvider` can:
1. Add documents and create an index
2. Retrieve relevant documents
3. Handle empty index gracefully

**Step 8: Run tests and commit**

```bash
git commit -m "feat: upgrade RAG from hash pseudo-embeddings to sentence-transformers"
```

---

## Task 8: KnowledgeGraph Hot-Reload Support

**Files:**
- Modify: `backend/app/graph/knowledge_graph.py`

**Step 1: Add reload method**

Add `reload(modules_dir: str)` method to KnowledgeGraph that:
1. Clears `_graph` and `_point_meta`
2. Re-calls `load_from_yaml(modules_dir)`
3. Logs the reload event

**Step 2: Add API endpoint for hot-reload**

Add `POST /api/v1/curriculum/reload` endpoint that:
1. Calls `knowledge_graph.reload()`
2. Resets cached teaching state
3. Returns updated module count

**Step 3: Commit**

```bash
git commit -m "feat: add KnowledgeGraph hot-reload support"
```

---

## Task 9: End-to-End Integration Test

**Files:**
- Create: `tests/e2e/test_narrative_flow.py`

**Step 1: Write E2E test**

Test the complete narrative flow:
1. Create a character and material
2. Start a conversation via WebSocket
3. Send a chat message, receive token stream
4. Trigger an assessment via `assessment.start`
5. Submit answers via `assessment.answer`
6. Receive `progress.update` with mastery change
7. Switch scenes via `scene.switch`
8. Request `state.sync` and verify full state

**Step 2: Run all tests**

Run: `python -m pytest tests/ -v --tb=short`
Expected: ALL PASS

**Step 3: Update PROGRESS.md**

Mark Phase 2.0 as complete with commit hash.

**Step 4: Final commit and push**

```bash
git commit -m "feat: Phase 2.0 complete — AssessmentEngine, Scene/Exam UI, RAG upgrade"
git push origin main
```