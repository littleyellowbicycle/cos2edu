"""核心教学引擎单元测试：AssessmentEngine 掌握度判定、EmotionEngine 情感衰减、
NarrativeEngine 教学编排。全程不调用真实 LLM/外部服务（LLMProvider 全部 mock）。
"""
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock

import pytest

from app.engines.assessment_engine import AssessmentEngine, QuizResult
from app.engines.emotion_engine import EmotionEngine, EmotionUpdate, _coerce_delta
from app.engines.narrative_engine import NarrativeEngine
from app.engines.world_state_engine import WorldStateEngine
from app.engines.character_engine import CharacterEngine, CharacterConfig
from app.engines.teaching_engine import TeachingEngine
from app.llm.context_budget import ContextBudget
from app.state.state_manager import StateManager
from app.graph.knowledge_graph import KnowledgeGraph
from app.services.chat_service import LLMProvider

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "content")


def make_character_config(cid: str = "ganyu") -> CharacterConfig:
    return CharacterConfig(
        id=cid,
        name="甘雨",
        teaching_style="narrative_guided",
        personality="温柔耐心的叙事型导师",
        background="千年历史的见证者",
        system_prompt_template="你是甘雨。",
        emotion_profile={
            "base_mood": 0.7,
            "mood_decay": 0.02,
            "event_sensitivity": {
                "student_correct": 0.05,
                "student_wrong": -0.02,
                "student_engaged": 0.08,
                "time_pressure": -0.1,
            },
        },
        relationship_dynamics={
            "trust_growth_rate": 0.01,
            "trust_decay_rate": 0.005,
            "max_trust": 1.0,
        },
    )


def make_character_engine() -> CharacterEngine:
    engine = CharacterEngine(CONTENT_DIR)
    engine._characters = {"ganyu": make_character_config()}
    return engine


# --------------------------------------------------------------------------- #
# AssessmentEngine — 掌握度判定
# --------------------------------------------------------------------------- #

class TestAssessmentMastery:

    def setup_method(self):
        self.engine = AssessmentEngine()

    def test_high_scores_pass_as_mastered(self):
        result = self.engine.assess_point("kp_a", scores=[1.0, 0.9, 0.8], attempts=1)
        assert result.passed is True
        assert result.mastery_level >= AssessmentEngine.MASTERY_THRESHOLD
        assert result.status == "mastered"
        assert "掌握" in result.feedback

    def test_low_scores_learning_not_passed(self):
        result = self.engine.assess_point("kp_a", scores=[0.2, 0.3], attempts=1)
        assert result.passed is False
        assert result.status == "learning"

    def test_repeated_attempts_penalize_mastery(self):
        first = self.engine.calculate_mastery([0.9, 0.9], attempts=1)
        penalized = self.engine.calculate_mastery([0.9, 0.9], attempts=3)
        assert penalized < first
        assert penalized >= 0.0

    def test_max_attempts_low_mastery_is_review_needed(self):
        result = self.engine.assess_point("kp_a", scores=[0.3, 0.3], attempts=AssessmentEngine.MAX_ATTEMPTS)
        assert result.passed is False
        assert result.status == "review_needed"

    def test_empty_scores_zero_mastery(self):
        result = self.engine.assess_point("kp_a", scores=[], attempts=1)
        assert result.mastery_level == 0.0
        assert result.passed is False

    def test_mastery_capped_between_zero_and_one(self):
        assert self.engine.calculate_mastery([1.0], attempts=1) <= 1.0
        assert self.engine.calculate_mastery([0.0], attempts=10) >= 0.0

    def test_evaluate_answer_choice_exact_match(self):
        q = {"question_type": "choice", "correct_answer": "选项A", "explanation": ""}
        ok = self.engine.evaluate_answer(q, "选项A")
        assert ok["is_correct"] is True
        assert ok["score"] == 1.0
        bad = self.engine.evaluate_answer(q, "选项B")
        assert bad["is_correct"] is False
        assert bad["score"] == 0.0

    def test_evaluate_answer_open_keyword_overlap(self):
        q = {"question_type": "open", "correct_answer": "梯度, 反向传播", "explanation": ""}
        hit = self.engine.evaluate_answer(q, "通过梯度进行反向传播")
        assert hit["is_correct"] is True
        miss = self.engine.evaluate_answer(q, "我认为就是记忆")
        assert miss["is_correct"] is False

    def test_should_trigger_assessment_rules(self):
        # 已掌握的知识点不再触发
        assert self.engine.should_trigger_assessment("a", {"a"}, message_count=5) is False
        # 消息数不足
        assert self.engine.should_trigger_assessment("a", set(), message_count=3) is False
        # 非 5 的倍数
        assert self.engine.should_trigger_assessment("a", set(), message_count=4) is False
        # 正常触发
        assert self.engine.should_trigger_assessment("a", set(), message_count=5) is True

    def test_score_quiz_boundaries(self):
        r = self.engine.score_quiz("a", total_questions=4, correct_answers=3)
        assert isinstance(r, QuizResult)
        assert r.passed is True
        fail = self.engine.score_quiz("a", total_questions=4, correct_answers=1)
        assert fail.passed is False
        zero = self.engine.score_quiz("a", total_questions=0, correct_answers=0)
        assert zero.passed is False
        assert zero.mastery_level == 0.0


# --------------------------------------------------------------------------- #
# EmotionEngine — 情感更新与衰减
# --------------------------------------------------------------------------- #

class TestEmotionEngine:

    def setup_method(self):
        self.char_engine = make_character_engine()
        self.emotion = EmotionEngine(self.char_engine)

    def test_initialized_from_character_profile(self):
        state = self.emotion.get_state("ganyu")
        assert abs(state.mood - 0.7) < 1e-6
        assert abs(state.trust - 0.01) < 1e-6  # trust_growth_rate seeded as initial trust

    def test_student_correct_raises_mood_and_trust(self):
        update = self.emotion.update("ganyu", "student_correct", 0.05)
        assert isinstance(update, EmotionUpdate)
        assert update.mood > 0.7
        assert update.mood_delta > 0
        assert self.emotion.get_trust("ganyu") > 0.01

    def test_student_wrong_lowers_mood_and_trust(self):
        update = self.emotion.update("ganyu", "student_wrong", -0.02)
        assert update.mood < 0.7
        assert update.mood_delta < 0
        assert self.emotion.get_trust("ganyu") < 0.01

    def test_unknown_character_returns_none(self):
        assert self.emotion.update("nobody", "student_correct") is None
        assert self.emotion.apply_decay("nobody") is None

    def test_mood_clamped_at_one(self):
        for _ in range(50):
            self.emotion.update("ganyu", "student_correct", 0.5)
        assert self.emotion.get_mood("ganyu") <= 1.0

    def test_string_quoted_sensitivity_coerced(self):
        """回归：YAML 把 +0.08 读成字符串时不应在 mood 累加时抛 TypeError。"""
        char_engine = CharacterEngine(CONTENT_DIR)
        char_engine._characters = {
            "str_char": CharacterConfig(
                id="str_char", name="字符串导师", teaching_style="",
                personality="", background="", system_prompt_template="",
                emotion_profile={
                    "base_mood": 0.7,
                    "mood_decay": "0.02",
                    "event_sensitivity": {"student_engaged": "+0.08"},
                },
                relationship_dynamics={"trust_growth_rate": "0.01", "max_trust": "1.0"},
            )
        }
        engine = EmotionEngine(char_engine)
        update = engine.update("str_char", "student_engaged")
        assert update is not None
        assert update.mood > 0.7
        decay = engine.apply_decay("str_char", hours_elapsed=1.0)
        assert decay.mood < update.mood

    def test_apply_decay_scales_with_hours_and_floors(self):
        self.emotion.update("ganyu", "student_correct", 0.3)  # mood -> 1.0 (clamped)
        before = self.emotion.get_mood("ganyu")
        decay_short = self.emotion.apply_decay("ganyu", hours_elapsed=1.0)
        decay_long = self.emotion.apply_decay("ganyu", hours_elapsed=10.0)
        assert decay_short.mood < before
        assert decay_long.mood < decay_short.mood
        # 地板为 base_mood - 0.1，不会无限下跌
        assert self.emotion.get_mood("ganyu") >= 0.7 - 0.1 - 1e-6

    def test_get_all_states_contains_character(self):
        states = self.emotion.get_all_states()
        assert "ganyu" in states
        assert states["ganyu"]["mood"] >= 0.0

    def test_coerce_delta_helper(self):
        assert _coerce_delta("+0.05", 0.0) == 0.05
        assert _coerce_delta("-0.02", 0.0) == -0.02
        assert _coerce_delta(0.1, 0.0) == 0.1
        assert _coerce_delta("garbage", 0.3) == 0.3


# --------------------------------------------------------------------------- #
# NarrativeEngine — 教学编排（mock LLMProvider，不联网）
# --------------------------------------------------------------------------- #

class _FakeUow:
    """绑定 test_session 的轻量 UoW，满足 NarrativeEngine 内的仓储访问。"""

    def __init__(self, session):
        from app.repositories.conversation_repository import ConversationRepository
        from app.repositories.message_repository import MessageRepository
        from app.repositories.model_config_repository import ModelConfigRepository
        self.session = session
        self.conversations = ConversationRepository(session)
        self.messages = MessageRepository(session)
        self.model_configs = ModelConfigRepository(session)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.commit()
        return False


class _FakeConfigUow:
    """Async context manager exposing a default model config for generate_quiz."""

    def __init__(self, config):
        self._config = config
        self.model_configs = SimpleNamespace(get_default=AsyncMock(return_value=config))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def build_engine(session=None, mocker=None) -> NarrativeEngine:
    kg = KnowledgeGraph()
    world = WorldStateEngine(content_dir=CONTENT_DIR)
    characters = make_character_engine()
    teaching = TeachingEngine(kg, characters, ContextBudget(total_tokens=2048))
    emotion = EmotionEngine(characters)
    engine = NarrativeEngine(
        knowledge_graph=kg,
        world_state_engine=world,
        character_engine=characters,
        teaching_engine=teaching,
        state_manager=MagicMock(spec=StateManager),
        emotion_engine=emotion,
        assessment_engine=AssessmentEngine(kg, characters),
    )
    engine.rag = MagicMock(get_context=MagicMock(return_value=""))
    if session is not None and mocker is not None:
        import app.engines.narrative_engine as ne_module
        mocker.patch.object(ne_module, "UnitOfWork", lambda: _FakeUow(session))
    return engine


class TestNarrativeOrchestration:

    def test_free_chat_prompt_uses_character_persona(self):
        engine = build_engine()
        messages = engine._build_default_prompt(
            character_id="ganyu",
            history=[{"role": "user", "content": "问题1"}],
            rag_context="参考资料片段",
        )
        assert messages[0]["role"] == "system"
        assert "温柔耐心" in messages[0]["content"]
        # RAG 上下文作为额外 system 消息注入
        assert any("参考资料片段" in m["content"] for m in messages)

    def test_free_chat_prompt_unknown_character_fallback(self):
        engine = build_engine()
        messages = engine._build_default_prompt(character_id="ghost", history=[])
        assert "苏格拉底" in messages[0]["content"]

    def test_structured_prompt_uses_scene_and_point(self):
        engine = build_engine()
        engine.graph._point_meta["kp_a"] = MagicMock(
            id="kp_a", name="感知机", module_id="m1", module_name="基础",
            difficulty=1, estimated_minutes=30, key_concepts=["线性分类"],
            teaching_hints={}, suggested_questions=[], exercises=[], prerequisites=[],
        )
        point_data = {
            "point_id": "kp_a", "name": "感知机", "module_name": "基础",
            "difficulty": 1, "key_concepts": ["线性分类"], "teaching_hints": {},
            "suggested_questions": [], "exercises": [],
        }
        messages = engine._build_default_prompt(
            character_id="ganyu", history=[], point_data=point_data,
        )
        combined = "\n".join(m["content"] for m in messages)
        assert "线性分类" in combined
        # 场景规则被注入
        assert "classroom" in combined or "teach" in combined

    def test_emotion_keyword_routing(self):
        engine = build_engine()
        engine.emotion = MagicMock(wraps=engine.emotion)
        engine._update_emotion_after_response("ganyu", "回复", "是的，我明白了")
        engine.emotion.update.assert_called_once_with("ganyu", "student_correct", 0.05)

        engine.emotion.reset_mock()
        engine._update_emotion_after_response("ganyu", "回复", "我不懂这个概念")
        engine.emotion.update.assert_called_once_with("ganyu", "student_wrong", -0.02)

        engine.emotion.reset_mock()
        engine._update_emotion_after_response("ganyu", "回复", "今天天气如何")
        engine.emotion.update.assert_not_called()

    def test_mood_to_description_thresholds(self):
        engine = build_engine()
        assert "兴奋" in engine._mood_to_description(0.9)
        assert "不安" in engine._mood_to_description(0.1)

    def test_start_and_submit_assessment_scoring(self):
        engine = build_engine()
        engine.graph._point_meta["kp_a"] = MagicMock(
            id="kp_a", name="感知机", module_id="m1", module_name="基础",
            difficulty=1, estimated_minutes=30, key_concepts=["线性分类"],
            teaching_hints={}, suggested_questions=["什么是感知机？"],
            exercises=[], prerequisites=[],
        )
        engine.graph._graph["kp_a"] = set()
        quiz = engine.start_assessment("kp_a", num_questions=2)
        assert len(quiz.questions) >= 1
        result = engine.submit_assessment_answer("kp_a", [0] * len(quiz.questions))
        assert isinstance(result, QuizResult)
        assert result.knowledge_point_id == "kp_a"
        assert "kp_a" not in engine._active_quizzes

    @pytest.mark.asyncio
    async def test_generate_quiz_uses_mocked_llm_json(self, mocker):
        engine = build_engine()
        engine.graph._point_meta["kp_a"] = MagicMock(
            id="kp_a", name="感知机", module_id="m1", module_name="基础",
            difficulty=1, estimated_minutes=30, key_concepts=["线性分类"],
            teaching_hints={}, suggested_questions=[], exercises=[], prerequisites=[],
        )
        mocker.patch.object(
            LLMProvider, "chat",
            new=AsyncMock(return_value='{"questions": [{"question_text": "Q1"}]}'),
        )
        # 替换 UnitOfWork：返回带默认模型配置的假 uow，避免真实 DB/LLM
        import app.engines.narrative_engine as ne_module
        fake_uow = _FakeConfigUow(SimpleNamespace(
            provider="openai", model_name="gpt-4", api_key="k",
            base_url=None, group_id=None,
        ))
        mocker.patch.object(ne_module, "UnitOfWork", lambda: fake_uow)
        result = await engine.generate_quiz("kp_a", "ganyu")
        assert "error" not in result
        assert result["quiz"]["questions"][0]["question_text"] == "Q1"

    @pytest.mark.asyncio
    async def test_generate_quiz_unknown_point_error(self):
        engine = build_engine()
        result = await engine.generate_quiz("missing", "ganyu")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_handle_assessment_answer_dict_payload_no_crash(self, mocker):
        """回归：dict 形态的答案载荷（{question, answer}）不应因元组解包崩溃。"""
        engine = build_engine()
        mocker.patch.object(
            engine, "_get_progress_for_point", AsyncMock(return_value=None)
        )
        answers = [
            {"question": {"question_type": "choice", "correct_answer": "A"}, "answer": "A"},
            {"question": {"question_type": "open", "correct_answer": "梯度"}, "answer": "沿梯度下降"},
            {"garbage": True},  # 畸形条目应被跳过
            ("not-a-dict", "A"),  # 畸形条目应被跳过
        ]
        result = await engine.handle_assessment_answer(
            conversation_id=1, point_id="kp_a", answers=answers, character_id="ganyu"
        )
        assert "error" not in result
        assert result["point_id"] == "kp_a"
        # 第一题答对 → 至少一个 1.0 分，掌握度非零
        assert result["score"] > 0

    @pytest.mark.asyncio
    async def test_handle_assessment_answer_tuple_payload_still_supported(self, mocker):
        engine = build_engine()
        mocker.patch.object(
            engine, "_get_progress_for_point", AsyncMock(return_value={"attempts": 2})
        )
        answers = [
            ({"question_type": "choice", "correct_answer": "A"}, "B"),
        ]
        result = await engine.handle_assessment_answer(
            conversation_id=1, point_id="kp_a", answers=answers, character_id="ganyu"
        )
        assert result["passed"] is False
        assert result["attempts"] == 3  # 累计 attempts + 1

    @pytest.mark.asyncio
    async def test_chat_stream_orchestrates_tokens_and_persists_messages(
        self, test_session, test_character, test_material, mocker
    ):
        engine = build_engine(test_session, mocker)

        from models.conversation import Conversation
        conv = Conversation(
            title="测试会话",
            character_id=test_character.id,
            material_id=test_material.id,
            teaching_mode="socratic",
        )
        test_session.add(conv)
        await test_session.commit()
        await test_session.refresh(conv)

        async def fake_stream(messages, tools=None):
            for chunk in ["思考", "引导", "提问"]:
                yield {"type": "text", "content": chunk}

        mocker.patch.object(LLMProvider, "chat_stream", side_effect=fake_stream)

        events = []
        async for event_str in engine.handle_chat_message(
            conversation_id=conv.id,
            user_message="什么是机器学习？",
            character_id="ganyu",
        ):
            events.append(event_str)

        import json
        parsed = [json.loads(e) for e in events]
        token_events = [e for e in parsed if e["type"] == "chat.token"]
        complete = [e for e in parsed if e["type"] == "chat.complete"]
        assert len(token_events) == 3
        assert complete and "思考引导提问" in complete[0]["content"]

        # 用户与助手消息均已落库
        from app.repositories.message_repository import MessageRepository
        repo = MessageRepository(test_session)
        msgs = await repo.get_by_conversation(conv.id)
        roles = [m.role for m in msgs]
        assert "user" in roles and "assistant" in roles

        # 情感更新事件被发出
        assert any(e["type"] == "emotion.update" for e in parsed)
