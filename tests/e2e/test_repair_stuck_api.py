"""repair-stuck REST 端点冒烟测试：空队列与有卡死材料两种情形，全部内存 SQLite。"""
import os
import sys

os.environ["APP_ENV"] = "test"

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "backend"))

import pytest
from httpx import AsyncClient, ASGITransport
from tests.helpers.test_app import create_test_engine, create_test_app_with_engine


@pytest.fixture(scope="function")
async def client():
    engine = create_test_engine()
    test_app, session_factory = await create_test_app_with_engine(engine)
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test"
    ) as c:
        yield c, session_factory, engine
    await engine.dispose()


@pytest.mark.asyncio
async def test_repair_stuck_empty_queue_returns_zero(client):
    c, session_factory, _ = client
    resp = await c.post("/api/v1/crud/materials/repair-stuck")
    assert resp.status_code == 200
    data = resp.json()
    assert data["repaired"] == 0
    assert data["message"] == "没有卡住的教学材料"


@pytest.mark.asyncio
async def test_repair_stuck_lists_stuck_material(client, monkeypatch):
    """有卡死材料时端点返回 repaired/failed 清单；不真正触发后台 LLM 任务。"""
    c, session_factory, engine = client

    # 直接在内存库里造一条 parsing 状态、无内容的卡死教材
    from models.material import Material
    async with session_factory() as session:
        stuck = Material(title="卡死教材", status="parsing", content=None)
        session.add(stuck)
        await session.commit()
        await session.refresh(stuck)
        stuck_id = stuck.id

    # 无内容 → 直接判 failed，不调度重处理；端点返回清单
    resp = await c.post("/api/v1/crud/materials/repair-stuck")
    assert resp.status_code == 200
    data = resp.json()
    assert data["failed"] == [stuck_id]
    assert data["repaired"] == []


@pytest.mark.asyncio
async def test_repair_stuck_requeues_contentful_material(client, monkeypatch):
    c, session_factory, engine = client

    from models.material import Material
    async with session_factory() as session:
        stuck = Material(title="可修复教材", status="parsing", content="已有索引内容" * 10)
        session.add(stuck)
        await session.commit()
        await session.refresh(stuck)
        stuck_id = stuck.id

    # 拦截模块级 process_material，并替换调度器为同步收集，避免在测试循环外跑真实任务
    collected = []

    async def fake_reprocess(material_id, file_path, uow_factory, ws_notify=None, text=None):
        collected.append(material_id)

    import app.tasks.material_pipeline as pipeline_module
    monkeypatch.setattr(pipeline_module, "process_material", fake_reprocess)
    monkeypatch.setattr(
        pipeline_module.asyncio, "create_task",
        lambda coro: (coro.close(), collected.append(coro))[1],
    )

    resp = await c.post("/api/v1/crud/materials/repair-stuck")
    assert resp.status_code == 200
    data = resp.json()
    assert data["repaired"] == [stuck_id]
    assert data["failed"] == []
    # 后台重处理任务已被调度（协程被捕获，未真正执行）
    assert len(collected) == 1
