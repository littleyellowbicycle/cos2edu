"""教材处理状态机单元测试。

覆盖：
- parse → index → outline → quality_check → pending_review 正常路径（含真实文本文件解析）
- 异常路径：文件缺失、解析失败、索引阶段物料丢失、大纲生成失败/返回空、大纲质量校验不通过
- repair-stuck 卡死修复：有内容的重新入队、无内容的直接判失败、空队列
- 全程使用内存 SQLite + mock 的 LLM/解析器，不访问外部服务。
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.material import Material
from app.repositories.material_repository import MaterialRepository
from app.repositories.syllabus_repository import SyllabusRepository
from app.repositories.model_config_repository import ModelConfigRepository
from app.parsers.base import ParseResult, ParseErrorCode
from app.tasks.material_pipeline import (
    process_material,
    repair_stuck_materials,
    get_task_status,
    _generate_outline,
)
from app.services.chat_service import LLMProvider


# --------------------------------------------------------------------------- #
# 内存 UoW 适配：把 test_session 包装成 pipeline 期望的 uow_factory
# --------------------------------------------------------------------------- #

class _UowWrapper:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.materials = MaterialRepository(session)
        self.syllabuses = SyllabusRepository(session)
        self.model_configs = ModelConfigRepository(session)

    async def __aenter__(self) -> "_UowWrapper":
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.commit()
        return False


def make_uow_factory(session: AsyncSession):
    def factory():
        return _UowWrapper(session)
    return factory


class _FakeConfigUow:
    """Async context manager with a stub default model config for _generate_outline."""

    def __init__(self, config=None):
        self._config = config
        self.model_configs = SimpleNamespace(
            get_default=AsyncMock(return_value=config),
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _fake_config():
    return SimpleNamespace(
        provider="openai", model_name="gpt-4", api_key="k",
        base_url=None, group_id=None,
    )


def make_notify_collector() -> list:
    events: list = []

    def notify(payload: dict):
        events.append(payload)

    notify.events = events
    return notify


VALID_OUTLINE = {
    "name": "Python 基础入门",
    "total_days": 30,
    "modules": [
        {
            "id": "mod_basics",
            "name": "基础模块",
            "order": 1,
            "knowledge_points": [
                {
                    "id": "kp_syntax",
                    "name": "Python 语法基础",
                    "difficulty": 1,
                    "key_concepts": ["变量", "表达式"],
                    "prerequisites": [],
                },
                {
                    "id": "kp_functions",
                    "name": "函数定义",
                    "difficulty": 2,
                    "key_concepts": ["def", "参数"],
                    "prerequisites": ["kp_syntax"],
                },
            ],
        }
    ],
}

INVALID_OUTLINE_UNDECLARED_PREREQ = {
    "name": "坏大纲",
    "modules": [
        {
            "id": "mod1",
            "name": "模块一",
            "knowledge_points": [
                {
                    "id": "kp_a",
                    "name": "知识点A",
                    "prerequisites": ["kp_missing"],
                }
            ],
        }
    ],
}


@pytest.mark.asyncio
class TestPipelineHappyPaths:

    async def test_text_path_full_flow_to_pending_review(self, test_session: AsyncSession, mocker):
        material = Material(
            title="Python 基础",
            content="Python 是一门解释型语言。" * 20,
            status="parsing",
        )
        test_session.add(material)
        await test_session.commit()
        await test_session.refresh(material)

        mocker.patch(
            "app.tasks.material_pipeline._generate_outline",
            return_value=VALID_OUTLINE,
        )
        notify = make_notify_collector()

        await process_material(
            material_id=material.id,
            file_path="",
            uow_factory=make_uow_factory(test_session),
            ws_notify=notify,
            text=material.content,
        )

        await test_session.refresh(material)
        assert material.status == "pending_review"
        assert material.review_status == "pending"
        assert material.content  # 内容已落库
        assert material.char_count == len(material.content)

        task = get_task_status(material.id)
        assert task.status == "pending_review"

        # 大纲已写入 syllabuses 表
        async with _UowWrapper(test_session) as uow:
            syllabus = await uow.syllabuses.get_by_material_id(material.id)
        assert syllabus is not None
        assert syllabus.review_status == "pending"
        assert syllabus.content["name"] == "Python 基础入门"

        # WS 状态序列覆盖关键阶段
        statuses = [e["payload"]["status"] for e in notify.events if e["type"] == "material.status_changed"]
        assert "indexed" in statuses
        assert "quality_check" in statuses
        assert statuses[-1] == "pending_review"

    async def test_real_text_file_parsed_to_pending_review(self, test_session: AsyncSession, tmp_path, mocker):
        """使用真实 TextParser 解析磁盘上的 .txt 文件，验证 parse 阶段端到端。"""
        file_path = tmp_path / "lesson.txt"
        file_path.write_text(
            "机器学习是一门研究如何让计算机从数据中自动学习规律的学科。" * 10,
            encoding="utf-8",
        )

        material = Material(title="机器学习讲义", status="parsing")
        test_session.add(material)
        await test_session.commit()
        await test_session.refresh(material)

        mocker.patch(
            "app.tasks.material_pipeline._generate_outline",
            return_value=VALID_OUTLINE,
        )
        notify = make_notify_collector()

        await process_material(
            material_id=material.id,
            file_path=str(file_path),
            uow_factory=make_uow_factory(test_session),
            ws_notify=notify,
        )

        await test_session.refresh(material)
        assert material.status == "pending_review"
        assert material.content  # 解析出的文本已落库
        assert material.char_count > 0


# --------------------------------------------------------------------------- #
# Happy-path 参数化矩阵：输入来源(text / 真实文件) × 大纲形态(单知识点 / 链式依赖 / 多模块)
# --------------------------------------------------------------------------- #

OUTLINE_SIMPLE = {
    "name": "单模块大纲",
    "modules": [
        {"id": "m1", "name": "模块一", "knowledge_points": [
            {"id": "kp_a", "name": "知识点A", "prerequisites": []},
        ]},
    ],
}

OUTLINE_CHAIN = {
    "name": "链式大纲",
    "modules": [
        {"id": "m1", "name": "模块一", "knowledge_points": [
            {"id": "kp_a", "name": "起点", "prerequisites": []},
            {"id": "kp_b", "name": "后继", "prerequisites": ["kp_a"]},
            {"id": "kp_c", "name": "终点", "prerequisites": ["kp_b"]},
        ]},
    ],
}

OUTLINE_MULTI_MODULE = {
    "name": "多模块大纲",
    "modules": [
        {"id": "m1", "name": "基础", "order": 1, "knowledge_points": [
            {"id": "kp_a", "name": "A", "prerequisites": []},
        ]},
        {"id": "m2", "name": "进阶", "order": 2, "knowledge_points": [
            {"id": "kp_b", "name": "B", "prerequisites": ["kp_a"]},
        ]},
    ],
}


@pytest.mark.asyncio
@pytest.mark.parametrize("source", ["text", "file"])
@pytest.mark.parametrize("outline", [OUTLINE_SIMPLE, OUTLINE_CHAIN, OUTLINE_MULTI_MODULE],
                         ids=["simple", "chain", "multi_module"])
class TestHappyPathMatrix:

    async def test_matrix_reaches_pending_review(self, test_session: AsyncSession, tmp_path,
                                                  mocker, source, outline):
        body = "机器学习是一门研究如何让计算机从数据中自动学习规律的学科。" * 10
        mocker.patch("app.tasks.material_pipeline._generate_outline", return_value=outline)
        notify = make_notify_collector()

        kwargs = {"uow_factory": make_uow_factory(test_session), "ws_notify": notify}
        if source == "text":
            material = Material(title="矩阵教材", content=body, status="parsing")
            test_session.add(material)
            await test_session.commit()
            await test_session.refresh(material)
            kwargs["text"] = body
            kwargs["file_path"] = ""
        else:
            file_path = tmp_path / "matrix.txt"
            file_path.write_text(body, encoding="utf-8")
            material = Material(title="矩阵文件教材", status="parsing")
            test_session.add(material)
            await test_session.commit()
            await test_session.refresh(material)
            kwargs["file_path"] = str(file_path)

        await process_material(material_id=material.id, **kwargs)

        await test_session.refresh(material)
        assert material.status == "pending_review"
        assert material.review_status == "pending"
        assert material.content
        if source == "text":
            assert material.char_count == len(body)
        else:
            assert material.char_count > 0

        async with _UowWrapper(test_session) as uow:
            syllabus = await uow.syllabuses.get_by_material_id(material.id)
        assert syllabus is not None
        assert syllabus.content["name"] == outline["name"]

        statuses = [e["payload"]["status"] for e in notify.events if e["type"] == "material.status_changed"]
        assert "quality_check" in statuses
        assert statuses[-1] == "pending_review"


@pytest.mark.asyncio
class TestPipelineParseFailures:

    async def test_missing_file_fails_with_error_code(self, test_session: AsyncSession):
        material = Material(title="缺失文件教材", status="parsing")
        test_session.add(material)
        await test_session.commit()
        await test_session.refresh(material)
        notify = make_notify_collector()

        await process_material(
            material_id=material.id,
            file_path="/does/not/exist.txt",
            uow_factory=make_uow_factory(test_session),
            ws_notify=notify,
        )

        await test_session.refresh(material)
        assert material.status == "failed"
        assert material.error_code == ParseErrorCode.UNKNOWN_ERROR
        task = get_task_status(material.id)
        assert task.status == "failed"
        assert task.error_message
        # 失败事件已通过 WS 上报
        assert notify.events[-1]["payload"]["status"] == "failed"

    async def test_parser_reports_failure_code(self, test_session: AsyncSession, mocker):
        material = Material(title="损坏 PDF", status="parsing")
        test_session.add(material)
        await test_session.commit()
        await test_session.refresh(material)

        from app.parsers.parser_registry import parser_registry
        mocker.patch.object(
            parser_registry,
            "parse",
            return_value=ParseResult(
                success=False,
                error_code=ParseErrorCode.PDF_CORRUPTED,
                error_message="PDF 文件已损坏",
                suggestion="请重新上传",
            ),
        )
        notify = make_notify_collector()

        await process_material(
            material_id=material.id,
            file_path="corrupt.pdf",
            uow_factory=make_uow_factory(test_session),
            ws_notify=notify,
        )

        await test_session.refresh(material)
        assert material.status == "failed"
        assert material.error_code == ParseErrorCode.PDF_CORRUPTED
        task = get_task_status(material.id)
        assert task.error_code == ParseErrorCode.PDF_CORRUPTED
        assert task.error_message == "PDF 文件已损坏"


@pytest.mark.asyncio
class TestPipelineIndexAndOutlineFailures:

    async def test_missing_material_at_index_phase_ends_failed(self, test_session: AsyncSession):
        """索引阶段物料已被删除：不应静默成功，任务应进入 failed。"""
        notify = make_notify_collector()

        await process_material(
            material_id=999999,
            file_path="",
            uow_factory=make_uow_factory(test_session),
            ws_notify=notify,
            text="一些教材内容" * 20,
        )

        task = get_task_status(999999)
        assert task.status == "failed"
        assert task.error_message

    async def test_index_phase_db_error_is_caught_and_failed(self, test_session: AsyncSession, mocker):
        material = Material(title="DB异常教材", status="parsing", content="x" * 200)
        test_session.add(material)
        await test_session.commit()
        await test_session.refresh(material)

        async def boom(*args, **kwargs):
            raise RuntimeError("database connection lost")

        mocker.patch.object(MaterialRepository, "update", side_effect=boom)
        notify = make_notify_collector()

        await process_material(
            material_id=material.id,
            file_path="",
            uow_factory=make_uow_factory(test_session),
            ws_notify=notify,
            text=material.content,
        )

        task = get_task_status(material.id)
        assert task.status == "failed"
        assert "database connection lost" in task.error_message

    async def test_outline_exception_falls_back_to_indexed(self, test_session: AsyncSession, mocker):
        material = Material(title="无模型教材", status="parsing", content="内容" * 100)
        test_session.add(material)
        await test_session.commit()
        await test_session.refresh(material)

        mocker.patch(
            "app.tasks.material_pipeline._generate_outline",
            side_effect=ValueError("未配置默认AI模型"),
        )
        notify = make_notify_collector()

        await process_material(
            material_id=material.id,
            file_path="",
            uow_factory=make_uow_factory(test_session),
            ws_notify=notify,
            text=material.content,
        )

        await test_session.refresh(material)
        # 大纲失败不阻断索引成果：物料保持 indexed，可自由对话
        assert material.status == "indexed"
        task = get_task_status(material.id)
        assert task.status == "indexed"
        assert "大纲生成失败" in task.progress_message

        async with _UowWrapper(test_session) as uow:
            syllabus = await uow.syllabuses.get_by_material_id(material.id)
        assert syllabus is None

    async def test_outline_none_falls_back_to_indexed(self, test_session: AsyncSession, mocker):
        material = Material(title="空大纲教材", status="parsing", content="内容" * 100)
        test_session.add(material)
        await test_session.commit()
        await test_session.refresh(material)

        mocker.patch(
            "app.tasks.material_pipeline._generate_outline",
            return_value=None,
        )

        await process_material(
            material_id=material.id,
            file_path="",
            uow_factory=make_uow_factory(test_session),
            ws_notify=make_notify_collector(),
            text=material.content,
        )

        await test_session.refresh(material)
        assert material.status == "indexed"


@pytest.mark.asyncio
class TestQualityCheckStage:

    async def test_invalid_outline_rejected_with_notification(self, test_session: AsyncSession, mocker):
        material = Material(title="坏大纲教材", status="parsing", content="内容" * 100)
        test_session.add(material)
        await test_session.commit()
        await test_session.refresh(material)

        mocker.patch(
            "app.tasks.material_pipeline._generate_outline",
            return_value=INVALID_OUTLINE_UNDECLARED_PREREQ,
        )
        notify = make_notify_collector()

        await process_material(
            material_id=material.id,
            file_path="",
            uow_factory=make_uow_factory(test_session),
            ws_notify=notify,
            text=material.content,
        )

        await test_session.refresh(material)
        assert material.status == "review_rejected"
        assert material.review_status == "rejected"
        assert material.error_code == "UNDECLARED_PREREQUISITE"

        task = get_task_status(material.id)
        assert task.status == "review_rejected"
        assert task.quality_reasons
        assert any("kp_missing" in r for r in task.quality_reasons)

        # 专用拒绝事件已通过通知机制上报原因
        rejected = [e for e in notify.events if e["type"] == "material.quality_rejected"]
        assert len(rejected) == 1
        assert rejected[0]["payload"]["status"] == "review_rejected"
        assert rejected[0]["payload"]["reasons"]

    async def test_rag_indexing_failure_is_non_fatal(self, test_session: AsyncSession, mocker):
        """RAG 分块失败只记 warning，不应阻断主流程（回归：RAG 异常曾被静默）。"""
        material = Material(title="RAG故障教材", status="parsing", content="内容" * 100)
        test_session.add(material)
        await test_session.commit()
        await test_session.refresh(material)

        mocker.patch(
            "app.tasks.material_pipeline._generate_outline",
            return_value=VALID_OUTLINE,
        )
        mocker.patch(
            "app.tasks.material_pipeline.get_rag_service",
            side_effect=RuntimeError("faiss unavailable"),
        )

        await process_material(
            material_id=material.id,
            file_path="",
            uow_factory=make_uow_factory(test_session),
            ws_notify=make_notify_collector(),
            text=material.content,
        )

        await test_session.refresh(material)
        assert material.status == "pending_review"

    async def test_raising_ws_notify_does_not_crash_pipeline(self, test_session: AsyncSession, mocker):
        """通知回调抛异常必须被吞掉，主流程照常完成（回归：WS 通知不应拖垮管线）。"""
        material = Material(title="通知故障教材", status="parsing", content="内容" * 100)
        test_session.add(material)
        await test_session.commit()
        await test_session.refresh(material)

        mocker.patch(
            "app.tasks.material_pipeline._generate_outline",
            return_value=VALID_OUTLINE,
        )

        def bad_notify(_payload):
            raise RuntimeError("websocket broken")

        await process_material(
            material_id=material.id,
            file_path="",
            uow_factory=make_uow_factory(test_session),
            ws_notify=bad_notify,
            text=material.content,
        )

        await test_session.refresh(material)
        assert material.status == "pending_review"

    async def test_validator_internal_error_degrades_to_indexed(self, test_session: AsyncSession, mocker):
        """校验器内部抛异常时管线降级为 indexed（自由对话），而不是整条 failed。"""
        material = Material(title="校验异常教材", status="parsing", content="内容" * 100)
        test_session.add(material)
        await test_session.commit()
        await test_session.refresh(material)

        mocker.patch(
            "app.tasks.material_pipeline._generate_outline",
            return_value=VALID_OUTLINE,
        )
        mocker.patch(
            "app.tasks.material_pipeline.validate_outline",
            side_effect=RuntimeError("validator exploded"),
        )
        notify = make_notify_collector()

        await process_material(
            material_id=material.id,
            file_path="",
            uow_factory=make_uow_factory(test_session),
            ws_notify=notify,
            text=material.content,
        )

        await test_session.refresh(material)
        assert material.status == "indexed"  # 降级，而非 failed
        task = get_task_status(material.id)
        assert task.status == "indexed"
        assert "降级" in task.progress_message
        # 异常未向上逃逸，WS 事件序列正常结束
        assert notify.events[-1]["payload"]["status"] == "indexed"

    async def test_rejected_outline_does_not_create_syllabus(self, test_session: AsyncSession, mocker):
        material = Material(title="坏大纲教材2", status="parsing", content="内容" * 100)
        test_session.add(material)
        await test_session.commit()
        await test_session.refresh(material)

        mocker.patch(
            "app.tasks.material_pipeline._generate_outline",
            return_value={"name": "无模块大纲", "modules": []},
        )

        await process_material(
            material_id=material.id,
            file_path="",
            uow_factory=make_uow_factory(test_session),
            ws_notify=make_notify_collector(),
            text=material.content,
        )

        await test_session.refresh(material)
        assert material.status == "review_rejected"
        async with _UowWrapper(test_session) as uow:
            assert await uow.syllabuses.get_by_material_id(material.id) is None


@pytest.mark.asyncio
class TestRepairStuck:

    async def test_repair_stuck_requeues_material_with_content(self, test_session: AsyncSession, mocker):
        stuck = Material(
            title="卡死教材",
            status="parsing",
            content="遗留的索引内容" * 10,
        )
        test_session.add(stuck)
        await test_session.commit()
        await test_session.refresh(stuck)

        mocker.patch(
            "app.tasks.material_pipeline._generate_outline",
            return_value=VALID_OUTLINE,
        )

        scheduled: list = []
        result = await repair_stuck_materials(
            uow_factory=make_uow_factory(test_session),
            schedule=lambda coro: scheduled.append(coro),
        )

        assert result["repaired"] == [stuck.id]
        assert result["failed"] == []
        assert len(scheduled) == 1

        # 直接 await 重新入队的协程（避免真实事件循环任务在测试结束时爆炸）
        await scheduled[0]

        await test_session.refresh(stuck)
        assert stuck.status == "pending_review"

    async def test_repair_stuck_marks_contentless_material_failed(self, test_session: AsyncSession):
        stuck = Material(title="无内容卡死教材", status="parsing", content=None)
        test_session.add(stuck)
        await test_session.commit()
        await test_session.refresh(stuck)

        scheduled: list = []
        result = await repair_stuck_materials(
            uow_factory=make_uow_factory(test_session),
            schedule=lambda coro: scheduled.append(coro),
        )

        assert result["failed"] == [stuck.id]
        assert result["repaired"] == []
        assert scheduled == []

        await test_session.refresh(stuck)
        assert stuck.status == "failed"
        assert stuck.error_code == "STUCK_NO_CONTENT"

    async def test_repair_stuck_empty_queue(self, test_session: AsyncSession):
        result = await repair_stuck_materials(
            uow_factory=make_uow_factory(test_session),
            schedule=lambda coro: (_ for _ in ()).throw(AssertionError("不应调度任务")),
        )
        assert result["stuck"] == []
        assert result["repaired"] == []
        assert result["failed"] == []

    async def test_repair_stuck_mixed_queue(self, test_session: AsyncSession, mocker):
        with_content = Material(
            title="可修复", status="parsing", content="已有内容" * 10,
        )
        without_content = Material(title="不可修复", status="parsing", content=None)
        test_session.add_all([with_content, without_content])
        await test_session.commit()
        await test_session.refresh(with_content)
        await test_session.refresh(without_content)

        mocker.patch(
            "app.tasks.material_pipeline._generate_outline",
            return_value=VALID_OUTLINE,
        )

        scheduled: list = []
        result = await repair_stuck_materials(
            uow_factory=make_uow_factory(test_session),
            schedule=lambda coro: scheduled.append(coro),
        )

        assert result["repaired"] == [with_content.id]
        assert result["failed"] == [without_content.id]
        assert len(scheduled) == 1

        await scheduled[0]
        await test_session.refresh(with_content)
        await test_session.refresh(without_content)
        assert with_content.status == "pending_review"
        assert without_content.status == "failed"


@pytest.mark.asyncio
class TestGenerateOutlineParsing:
    """_generate_outline 的响应清洗与 JSON 解析路径（mock LLMProvider.chat）。"""

    async def test_extracts_fenced_json_block(self, mocker):
        mocker.patch.object(
            LLMProvider, "chat",
            new=AsyncMock(return_value='```json\n{"name": "课程", "modules": []}\n```'),
        )
        factory = lambda: _FakeConfigUow(_fake_config())  # noqa: E731
        outline = await _generate_outline("教材内容", factory)
        assert outline["name"] == "课程"

    async def test_strips_think_tags_before_parsing(self, mocker):
        mocker.patch.object(
            LLMProvider, "chat",
            new=AsyncMock(return_value="<think>推理过程...</think>\n{\"name\": \"X\", \"modules\": []}"),
        )
        outline = await _generate_outline("教材内容", lambda: _FakeConfigUow(_fake_config()))
        assert outline["name"] == "X"

    async def test_empty_response_raises_value_error(self, mocker):
        mocker.patch.object(LLMProvider, "chat", new=AsyncMock(return_value=""))
        with pytest.raises(ValueError, match="空内容"):
            await _generate_outline("教材内容", lambda: _FakeConfigUow(_fake_config()))

    async def test_unparseable_json_raises_value_error(self, mocker):
        mocker.patch.object(LLMProvider, "chat", new=AsyncMock(return_value="这不是JSON"))
        with pytest.raises(ValueError, match="有效JSON|无法解析"):
            await _generate_outline("教材内容", lambda: _FakeConfigUow(_fake_config()))

    async def test_no_model_config_raises_value_error(self):
        with pytest.raises(ValueError, match="未配置"):
            await _generate_outline("教材内容", lambda: _FakeConfigUow(None))
