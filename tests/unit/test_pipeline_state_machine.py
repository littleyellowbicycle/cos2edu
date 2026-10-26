"""状态机衔接测试：quality_check → pending_review / → review_rejected 的完整事件序列，
以及重复触发、并发触发下的收敛一致性。使用真实内存 SQLite，每次调用独立会话。
"""
import asyncio
from typing import Optional

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.material import Material
from app.repositories.material_repository import MaterialRepository
from app.repositories.syllabus_repository import SyllabusRepository
from app.repositories.model_config_repository import ModelConfigRepository
from app.tasks.material_pipeline import process_material, get_task_status

from tests.unit.test_material_pipeline import VALID_OUTLINE, make_notify_collector

GOOD_OUTLINE = VALID_OUTLINE
BAD_OUTLINE = {
    "name": "坏大纲",
    "modules": [
        {"id": "m1", "name": "模块一",
         "knowledge_points": [{"id": "kp_a", "name": "A", "prerequisites": ["ghost"]}]}
    ],
}


class _SessionUow:
    """每次调用新建独立会话的 UoW，供并发触发使用。"""

    def __init__(self, session_factory):
        self._session_factory = session_factory
        self.session: Optional[AsyncSession] = None
        self.materials: Optional[MaterialRepository] = None
        self.syllabuses: Optional[SyllabusRepository] = None
        self.model_configs: Optional[ModelConfigRepository] = None

    async def __aenter__(self) -> "_SessionUow":
        self.session = self._session_factory()
        self.materials = MaterialRepository(self.session)
        self.syllabuses = SyllabusRepository(self.session)
        self.model_configs = ModelConfigRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is None:
            await self.session.commit()
        else:
            await self.session.rollback()
        await self.session.close()
        return False


def make_factory(session_factory):
    return lambda: _SessionUow(session_factory)


@pytest.fixture
def session_factory(test_engine):
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def _seed_material(session_factory, content: str) -> int:
    async with session_factory() as session:
        mat = Material(title="状态机教材", content=content, status="parsing")
        session.add(mat)
        await session.commit()
        await session.refresh(mat)
        return mat.id


async def _status_of(session_factory, material_id: int) -> Material:
    async with session_factory() as session:
        mat = await session.get(Material, material_id)
        await session.refresh(mat)
        return mat


def _status_sequence(notify) -> list[str]:
    return [e["payload"]["status"] for e in notify.events if e["type"] == "material.status_changed"]


@pytest.mark.asyncio
class TestTransitionToPendingReview:

    async def test_full_event_sequence_ends_pending_review(self, session_factory, mocker):
        mocker.patch("app.tasks.material_pipeline._generate_outline", return_value=GOOD_OUTLINE)
        mid = await _seed_material(session_factory, "教材正文" * 100)
        notify = make_notify_collector()

        await process_material(mid, "", make_factory(session_factory), ws_notify=notify, text="教材正文" * 100)

        seq = _status_sequence(notify)
        # 关键阶段按序出现：indexing → indexed → outlining → quality_check → pending_review
        assert seq.index("indexing") < seq.index("indexed")
        assert seq.index("indexed") < seq.index("outlining")
        assert "quality_check" in seq
        assert seq[-1] == "pending_review"

        mat = await _status_of(session_factory, mid)
        assert mat.status == "pending_review"
        assert mat.review_status == "pending"

        async with session_factory() as session:
            syllabus = await SyllabusRepository(session).get_by_material_id(mid)
        assert syllabus is not None
        assert syllabus.review_status == "pending"

    async def test_capabilities_flagged_throughout(self, session_factory, mocker):
        mocker.patch("app.tasks.material_pipeline._generate_outline", return_value=GOOD_OUTLINE)
        mid = await _seed_material(session_factory, "内容" * 100)
        notify = make_notify_collector()

        await process_material(mid, "", make_factory(session_factory), ws_notify=notify, text="内容" * 100)

        for event in notify.events:
            caps = event["payload"]["capabilities"]
            assert caps["structured_mode"] is False  # 未到 ready
        pending_event = [e for e in notify.events if e["payload"]["status"] == "pending_review"][-1]
        assert pending_event["payload"]["capabilities"]["free_chat"] is True


@pytest.mark.asyncio
class TestTransitionToReviewRejected:

    async def test_full_event_sequence_ends_review_rejected(self, session_factory, mocker):
        mocker.patch("app.tasks.material_pipeline._generate_outline", return_value=BAD_OUTLINE)
        mid = await _seed_material(session_factory, "内容" * 100)
        notify = make_notify_collector()

        await process_material(mid, "", make_factory(session_factory), ws_notify=notify, text="内容" * 100)

        seq = _status_sequence(notify)
        assert "quality_check" in seq
        assert seq[-1] == "review_rejected"

        mat = await _status_of(session_factory, mid)
        assert mat.status == "review_rejected"
        assert mat.review_status == "rejected"
        assert mat.error_code == "UNDECLARED_PREREQUISITE"

        # 专用拒绝事件携带原因
        rejected = [e for e in notify.events if e["type"] == "material.quality_rejected"]
        assert len(rejected) == 1
        assert rejected[0]["payload"]["status"] == "review_rejected"
        assert rejected[0]["payload"]["reasons"]
        assert "ghost" in rejected[0]["payload"]["reasons"][0]

        # 被拒大纲不落 syllabus
        async with session_factory() as session:
            assert await SyllabusRepository(session).get_by_material_id(mid) is None


@pytest.mark.asyncio
class TestDuplicateAndConcurrent:

    async def test_duplicate_trigger_converges_to_pending_review(self, session_factory, mocker):
        mocker.patch("app.tasks.material_pipeline._generate_outline", return_value=GOOD_OUTLINE)
        mid = await _seed_material(session_factory, "内容" * 100)

        # 第一次触发
        await process_material(mid, "", make_factory(session_factory), ws_notify=None, text="内容" * 100)
        # 第二次重复触发（模拟手动重跑 / repair-stuck 再次入队）
        await process_material(mid, "", make_factory(session_factory), ws_notify=None, text="内容" * 100)

        mat = await _status_of(session_factory, mid)
        assert mat.status == "pending_review"

        # 幂等：不堆积多条 syllabus
        async with session_factory() as session:
            from sqlalchemy import select, func
            from models.syllabus import Syllabus
            count = (await session.execute(select(func.count()).select_from(Syllabus).where(Syllabus.material_id == mid))).scalar_one()
        assert count == 1

    async def test_concurrent_triggers_both_finish_and_converge(self, session_factory, mocker):
        mocker.patch("app.tasks.material_pipeline._generate_outline", return_value=GOOD_OUTLINE)
        mid = await _seed_material(session_factory, "内容" * 100)

        errors = []

        async def runner():
            try:
                await process_material(mid, "", make_factory(session_factory), ws_notify=None, text="内容" * 100)
            except Exception as exc:  # 并发下任何未捕获异常都视为失败
                errors.append(exc)

        await asyncio.gather(runner(), runner())

        assert errors == []
        mat = await _status_of(session_factory, mid)
        # 收敛到终态之一（pending_review），不残留中间态
        assert mat.status == "pending_review"
        task = get_task_status(mid)
        assert task.status == "pending_review"
