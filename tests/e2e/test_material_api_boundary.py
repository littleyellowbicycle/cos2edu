"""受影响 REST / WS 端点的参数校验、状态守卫与边界测试。

REST：教材创建（空标题/超长字段 422、长度边界、404）、confirm/reject-syllabus
      状态守卫（非 pending_review → 400、不存在 → 404、pending_review → 200）、
      repair-stuck 空队列；WS：ping/pong、非法 JSON、缺字段、未知类型、
      syllabus.activate 缺 material_id、无引擎时的错误分支。

说明：本代码库无独立鉴权层（无 Bearer token / 用户依赖注入），所谓"未授权"在
      现有设计里体现为资源不存在 404 与状态不允许 400 的守卫，测试覆盖这两类。
全部内存 SQLite，不触达 LLM/Redis。
"""
import os
import sys
import json

os.environ["APP_ENV"] = "test"

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "backend"))

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.testclient import TestClient

from tests.helpers.test_app import create_test_engine
from models.material import Material


def _build_app(session_factory, engine):
    import app.core.database as db_module
    db_module.AsyncSessionLocal = session_factory
    db_module.engine = engine

    import app.repositories.unit_of_work as uow_module
    uow_module.AsyncSessionLocal = session_factory

    from app.api.v1.routes import router as crud_router
    from app.api.v1.curriculum import router as curriculum_router
    from app.api.v1.ws import router as ws_router

    app = FastAPI(title="Boundary Test App")
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )
    app.include_router(crud_router, prefix="/api/v1/crud", tags=["crud"])
    app.include_router(curriculum_router, prefix="/api/v1/curriculum", tags=["curriculum"])
    app.include_router(ws_router, prefix="/api/v1/ws", tags=["ws"])
    return app


@pytest.fixture(scope="function")
async def ctx():
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    from app.core.database import Base

    engine = create_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    app = _build_app(session_factory, engine)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client, session_factory
    await engine.dispose()


async def _seed_material(session_factory, *, status="parsing", content=None, title="测试教材") -> int:
    async with session_factory() as session:
        mat = Material(title=title, status=status, content=content)
        session.add(mat)
        await session.commit()
        await session.refresh(mat)
        return mat.id


# --------------------------------------------------------------------------- #
# REST：参数校验与超长字段
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
class TestMaterialValidation:

    async def test_empty_title_rejected_422(self, ctx):
        client, _ = ctx
        resp = await client.post("/api/v1/crud/materials", json={"title": "", "content": "x"})
        assert resp.status_code == 422

    async def test_overlong_title_rejected_422(self, ctx):
        client, _ = ctx
        resp = await client.post(
            "/api/v1/crud/materials",
            json={"title": "长" * 201, "content": "x"},
        )
        assert resp.status_code == 422

    async def test_title_at_max_length_accepted(self, ctx):
        client, _ = ctx
        resp = await client.post(
            "/api/v1/crud/materials",
            json={"title": "长" * 200, "content": "教材正文" * 10},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "长" * 200

    async def test_get_nonexistent_material_404(self, ctx):
        client, _ = ctx
        resp = await client.get("/api/v1/crud/materials/999999")
        assert resp.status_code == 404

    @pytest.mark.parametrize("payload,field", [
        ({"title": "正常标题", "description": "长" * 1001}, "description"),
        ({"title": "正常标题", "content_url": "u" * 501}, "content_url"),
        ({"title": "正常标题", "content_type": "t" * 21}, "content_type"),
    ])
    async def test_overlong_optional_fields_rejected_422(self, ctx, payload, field):
        client, _ = ctx
        resp = await client.post("/api/v1/crud/materials", json=payload)
        assert resp.status_code == 422
        # 422 响应中定位到越界字段
        body = resp.json()
        assert any(field in str(err.get("loc", [])) for err in body.get("detail", []))

    async def test_update_nonexistent_material_404(self, ctx):
        client, _ = ctx
        resp = await client.put(
            "/api/v1/crud/materials/999999", json={"title": "不存在"}
        )
        assert resp.status_code == 404


# --------------------------------------------------------------------------- #
# REST：confirm / reject-syllabus 状态守卫
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
class TestSyllabusStateGuards:

    async def test_confirm_on_indexed_state_rejected_400(self, ctx):
        client, session_factory = ctx
        mid = await _seed_material(session_factory, status="indexed", content="正文" * 50)
        resp = await client.post(f"/api/v1/curriculum/materials/{mid}/confirm-syllabus")
        assert resp.status_code == 400
        assert "不支持" in resp.json()["detail"]

    async def test_confirm_nonexistent_material_404(self, ctx):
        client, _ = ctx
        resp = await client.post("/api/v1/curriculum/materials/999999/confirm-syllabus")
        assert resp.status_code == 404

    async def test_reject_on_indexed_state_rejected_400(self, ctx):
        client, session_factory = ctx
        mid = await _seed_material(session_factory, status="indexed", content="正文" * 50)
        resp = await client.post(f"/api/v1/curriculum/materials/{mid}/reject-syllabus")
        assert resp.status_code == 400

    async def test_reject_nonexistent_material_404(self, ctx):
        client, _ = ctx
        resp = await client.post("/api/v1/curriculum/materials/999999/reject-syllabus")
        assert resp.status_code == 404

    async def test_confirm_on_pending_review_succeeds(self, ctx):
        client, session_factory = ctx
        mid = await _seed_material(session_factory, status="pending_review", content="正文" * 50)
        resp = await client.post(f"/api/v1/curriculum/materials/{mid}/confirm-syllabus")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        async with session_factory() as session:
            mat = await session.get(Material, mid)
            assert mat.status == "ready"
            assert mat.review_status == "approved"


# --------------------------------------------------------------------------- #
# REST：repair-stuck 空队列
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
class TestRepairStuckEndpoint:

    async def test_empty_queue_returns_zero(self, ctx):
        client, _ = ctx
        resp = await client.post("/api/v1/crud/materials/repair-stuck")
        assert resp.status_code == 200
        data = resp.json()
        assert data["repaired"] == 0
        assert "没有卡住" in data["message"]


# --------------------------------------------------------------------------- #
# WS：协议边界（无需 narrative engine，早期分支即可响应）
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="function")
def ws_app():
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

    # WS 早期分支（ping/非法JSON/缺字段/未知类型/无引擎）不触达数据库，
    # 因此这里不创建 aiosqlite 引擎，仅装配 app 与一个占位 session_factory。
    session_factory = async_sessionmaker(None, class_=AsyncSession, expire_on_commit=False)
    app = _build_app(session_factory, None)
    yield TestClient(app)


class TestWsProtocolBoundary:

    def test_ping_pong(self, ws_app):
        with ws_app.websocket_connect("/api/v1/ws/ws") as ws:
            ws.send_text(json.dumps({"type": "ping"}))
            data = json.loads(ws.receive_text())
            assert data["type"] == "pong"

    def test_malformed_json_returns_error(self, ws_app):
        with ws_app.websocket_connect("/api/v1/ws/ws") as ws:
            ws.send_text("{not valid json")
            data = json.loads(ws.receive_text())
            assert data["type"] == "error"

    def test_chat_send_missing_fields_returns_error(self, ws_app):
        with ws_app.websocket_connect("/api/v1/ws/ws") as ws:
            ws.send_text(json.dumps({"type": "chat.send", "payload": {}}))
            data = json.loads(ws.receive_text())
            assert data["type"] == "error"
            assert "conversation_id" in data["content"] or "content" in data["content"]

    def test_unknown_message_type_returns_error(self, ws_app):
        with ws_app.websocket_connect("/api/v1/ws/ws") as ws:
            ws.send_text(json.dumps({"type": "no.such.type", "payload": {}}))
            data = json.loads(ws.receive_text())
            assert data["type"] == "error"
            assert "未知" in data["content"]

    def test_syllabus_activate_missing_material_id_returns_error(self, ws_app):
        with ws_app.websocket_connect("/api/v1/ws/ws") as ws:
            ws.send_text(json.dumps({"type": "syllabus.activate", "payload": {}}))
            data = json.loads(ws.receive_text())
            assert data["type"] == "error"
            assert "material_id" in data["content"]

    def test_state_sync_without_engine_emits_empty_full_state(self, ws_app):
        with ws_app.websocket_connect("/api/v1/ws/ws") as ws:
            ws.send_text(json.dumps({"type": "state.sync", "payload": {}}))
            data = json.loads(ws.receive_text())
            assert data["type"] == "state.full"
            assert data["payload"] == {}

    def test_chat_send_without_engine_returns_error(self, ws_app):
        with ws_app.websocket_connect("/api/v1/ws/ws") as ws:
            ws.send_text(json.dumps({
                "type": "chat.send",
                "payload": {"conversation_id": 1, "content": "你好", "character_id": "ganyu"},
            }))
            data = json.loads(ws.receive_text())
            assert data["type"] == "error"
            assert "叙事引擎" in data["content"]
