"""F1–F6 缺陷的端到端回归测试：全部走真实内存 SQLite（test_session），
mock 仅用于替换 LLM/外部服务。每个测试编码"旧代码会违反、新代码满足"的断言。
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.material import Material
from app.tasks.material_pipeline import process_material, repair_stuck_materials, get_task_status
from app.engines.emotion_engine import EmotionEngine
from app.engines.character_engine import CharacterEngine, CharacterConfig
from app.engines.narrative_engine import NarrativeEngine
from app.engines.assessment_engine import AssessmentEngine
from app.engines.world_state_engine import WorldStateEngine
from app.engines.teaching_engine import TeachingEngine
from app.llm.context_budget import ContextBudget
from app.state.state_manager import StateManager
from app.graph.knowledge_graph import KnowledgeGraph

# 复用既有测试里的内存 UoW 适配与大纲夹具
from tests.unit.test_material_pipeline import (
    make_uow_factory,
    make_notify_collector,
    VALID_OUTLINE,
)

import os
CONTENT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "content")


async def _run_pipeline(session: AsyncSession, material: Material, outline, text: str, mocker):
    if outline is not None:
        mocker.patch("app.tasks.material_pipeline._generate_outline", return_value=outline)
    notify = make_notify_collector()
    await process_material(
        material_id=material.id,
        file_path="",
        uow_factory=make_uow_factory(session),
        ws_notify=notify,
        text=text,
    )
    await session.refresh(material)
    return notify


# --------------------------------------------------------------------------- #
# F1: 文本直送路径 char_count 恒为 0（旧代码：getattr 默认值不生效，写入 0）
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
class TestF1CharCountRegression:

    async def test_text_path_persists_real_char_count(self, test_session: AsyncSession, mocker):
        body = "Python 是一门解释型语言。" * 20  # 320 字
        material = Material(title="F1教材", content=body, status="parsing")
        test_session.add(material)
        await test_session.commit()
        await test_session.refresh(material)

        await _run_pipeline(test_session, material, VALID_OUTLINE, body, mocker)

        # 旧代码这里会是 0；修复后必须等于真实字数
        assert material.char_count == len(body)
        assert material.status == "pending_review"


# --------------------------------------------------------------------------- #
# F2: pending_review 更新作用在 detached 对象上（旧代码：状态不落库）
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
class TestF2DetachedUpdateRegression:

    async def test_pending_review_persisted_to_db(self, test_session: AsyncSession, mocker):
        body = "教材正文内容" * 50
        material = Material(title="F2教材", content=body, status="parsing")
        test_session.add(material)
        await test_session.commit()
        await test_session.refresh(material)

        await _run_pipeline(test_session, material, VALID_OUTLINE, body, mocker)

        # 旧代码 detached 更新丢失，DB 里仍是 indexed；修复后必须查到 pending_review
        fresh = await test_session.get(Material, material.id)
        assert fresh.status == "pending_review"
        assert fresh.review_status == "pending"

        # syllabus 也已落库
        from app.repositories.syllabus_repository import SyllabusRepository
        repo = SyllabusRepository(test_session)
        syllabus = await repo.get_by_material_id(material.id)
        assert syllabus is not None
        assert syllabus.review_status == "pending"


# --------------------------------------------------------------------------- #
# F3: 索引阶段物料缺失被静默跳过（旧代码：继续生成无主大纲）
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
class TestF3MissingMaterialRegression:

    async def test_missing_material_ends_failed_not_silent(self, test_session: AsyncSession, mocker):
        mocker.patch("app.tasks.material_pipeline._generate_outline", return_value=VALID_OUTLINE)
        notify = make_notify_collector()

        # 不存在的 material_id：旧代码会跳过索引并继续走到大纲阶段
        await process_material(
            material_id=424242,
            file_path="",
            uow_factory=make_uow_factory(test_session),
            ws_notify=notify,
            text="一些教材内容" * 20,
        )

        task = get_task_status(424242)
        assert task.status == "failed"
        assert task.error_message
        # 失败事件已上报，而不是静默 pending_review
        assert notify.events[-1]["payload"]["status"] == "failed"


# --------------------------------------------------------------------------- #
# F4: EmotionEngine 对 YAML 引号敏感度值崩溃（旧代码：str + float → TypeError）
# --------------------------------------------------------------------------- #

def _quoted_char_engine() -> CharacterEngine:
    engine = CharacterEngine(CONTENT_DIR)
    engine._characters = {
        "qchar": CharacterConfig(
            id="qchar", name="引号导师", teaching_style="",
            personality="", background="", system_prompt_template="",
            emotion_profile={
                "base_mood": "0.7",
                "mood_decay": "0.02",
                "event_sensitivity": {"student_engaged": "+0.08", "student_correct": "+0.05"},
            },
            relationship_dynamics={"trust_growth_rate": "0.01", "trust_decay_rate": "0.005", "max_trust": "1.0"},
        )
    }
    return engine


class TestF4QuotedSensitivityRegression:

    def test_quoted_plus_sensitivity_updates_without_typeerror(self):
        emotion = EmotionEngine(_quoted_char_engine())
        # 旧代码：current_mood(float) + "+0.08"(str) → TypeError
        update = emotion.update("qchar", "student_engaged")
        assert update is not None
        assert update.mood > 0.7
        # student_correct 按引号 trust_growth_rate("0.01") 累加信任度
        correct = emotion.update("qchar", "student_correct")
        assert correct.mood_delta > 0
        assert emotion.get_trust("qchar") > 0.01

    def test_quoted_decay_applies(self):
        emotion = EmotionEngine(_quoted_char_engine())
        emotion.update("qchar", "student_correct", 0.2)  # 抬升 mood
        before = emotion.get_mood("qchar")
        decay = emotion.apply_decay("qchar", hours_elapsed=2.0)
        assert decay.mood < before
        assert emotion.get_mood("qchar") >= 0.7 - 0.1 - 1e-6


# --------------------------------------------------------------------------- #
# F5: handle_assessment_answer 死查询 + dict 载荷解包崩溃（旧代码：ValueError）
# --------------------------------------------------------------------------- #

def _build_narrative_engine() -> NarrativeEngine:
    kg = KnowledgeGraph()
    world = WorldStateEngine(content_dir=CONTENT_DIR)
    characters = CharacterEngine(CONTENT_DIR)
    teaching = TeachingEngine(kg, characters, ContextBudget(total_tokens=2048))
    return NarrativeEngine(
        knowledge_graph=kg,
        world_state_engine=world,
        character_engine=characters,
        teaching_engine=teaching,
        state_manager=MagicMock(spec=StateManager),
        emotion_engine=EmotionEngine(characters),
        assessment_engine=AssessmentEngine(kg, characters),
    )


@pytest.mark.asyncio
class TestF5AssessmentPayloadRegression:

    async def test_dict_payload_does_not_crash(self, mocker):
        engine = _build_narrative_engine()
        mocker.patch.object(engine, "_get_progress_for_point", AsyncMock(return_value=None))

        # 旧代码 for q,a in answers 对 dict 解包 → ValueError
        result = await engine.handle_assessment_answer(
            conversation_id=1,
            point_id="kp_a",
            answers=[
                {"question": {"question_type": "choice", "correct_answer": "A"}, "answer": "A"},
                {"question": {"question_type": "open", "correct_answer": "梯度"}, "answer": "沿梯度下降"},
            ],
            character_id="qchar",
        )
        assert "error" not in result
        assert result["attempts"] == 1
        assert result["score"] > 0

    async def test_tuple_payload_still_supported(self, mocker):
        engine = _build_narrative_engine()
        mocker.patch.object(
            engine, "_get_progress_for_point",
            AsyncMock(return_value={"attempts": 2, "status": "learning", "mastery_level": 0.3}),
        )
        result = await engine.handle_assessment_answer(
            conversation_id=1, point_id="kp_a",
            answers=[({"question_type": "choice", "correct_answer": "A"}, "B")],
            character_id="qchar",
        )
        assert result["passed"] is False
        assert result["attempts"] == 3


# --------------------------------------------------------------------------- #
# F6: repair-stuck 对无内容卡死物料无解（旧代码：永久挂在 parsing）
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
class TestF6RepairStuckRegression:

    async def test_contentless_stuck_material_marked_failed(self, test_session: AsyncSession):
        stuck = Material(title="F6卡死教材", status="parsing", content=None)
        test_session.add(stuck)
        await test_session.commit()
        await test_session.refresh(stuck)

        scheduled = []
        result = await repair_stuck_materials(
            uow_factory=make_uow_factory(test_session),
            schedule=lambda coro: scheduled.append(coro),
        )

        assert result["failed"] == [stuck.id]
        assert result["repaired"] == []
        assert scheduled == []

        fresh = await test_session.get(Material, stuck.id)
        # 旧代码：永远停在 parsing；修复后 failed + STUCK_NO_CONTENT
        assert fresh.status == "failed"
        assert fresh.error_code == "STUCK_NO_CONTENT"

    async def test_contentful_stuck_material_requeued(self, test_session: AsyncSession, mocker):
        stuck = Material(title="F6可修复教材", status="parsing", content="已有索引内容" * 10)
        test_session.add(stuck)
        await test_session.commit()
        await test_session.refresh(stuck)

        mocker.patch("app.tasks.material_pipeline._generate_outline", return_value=VALID_OUTLINE)

        scheduled = []
        result = await repair_stuck_materials(
            uow_factory=make_uow_factory(test_session),
            schedule=lambda coro: scheduled.append(coro),
        )
        assert result["repaired"] == [stuck.id]
        assert len(scheduled) == 1

        await scheduled[0]
        fresh = await test_session.get(Material, stuck.id)
        assert fresh.status == "pending_review"
