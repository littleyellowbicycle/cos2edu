"""
端到端测试：从前端操作视角覆盖完整后端 API 流程。

覆盖的流程：
1. 基础端点（健康检查、提供商列表）
2. 角色管理完整流程 (CRUD + 软删除)
3. 教材管理完整流程 (CRUD + 文件上传)
4. 模型配置完整流程 (CRUD + 默认配置逻辑)
5. 背景配置完整流程 (CRUD)
6. 对话会话完整生命周期
7. 完整苏格拉底教学会话（模拟 LLM）
8. 错误场景（404、422 验证错误）
"""
import os
import sys

os.environ["APP_ENV"] = "test"

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

import pytest
from httpx import AsyncClient, ASGITransport
from tests.helpers.test_app import create_test_engine, create_test_app_with_engine


@pytest.fixture(scope="function")
async def client():
    engine = create_test_engine()
    test_app, _ = await create_test_app_with_engine(engine)
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test"
    ) as c:
        yield c
    await engine.dispose()


@pytest.fixture
def character_payload():
    return {
        "name": "爱因斯坦导师",
        "description": "一位以爱因斯坦为原型的物理教学导师",
        "personality": "幽默风趣，善于用生活实例解释复杂的物理概念",
        "background": "20世纪最伟大的物理学家之一",
        "avatar": "👨‍🔬",
        "avatar_type": "emoji"
    }


@pytest.fixture
def material_payload():
    return {
        "title": "量子力学入门",
        "description": "量子力学的基本概念和原理",
        "content": "量子力学是研究微观粒子运动规律的物理学分支。它的基本概念包括波粒二象性、不确定性原理、量子叠加和量子纠缠等。",
        "content_type": "text"
    }


@pytest.fixture
def model_config_payload():
    return {
        "provider": "openai",
        "model_name": "gpt-4.1",
        "api_key": "sk-test-key-12345",
        "base_url": "https://api.openai.com/v1",
        "is_default": True
    }


@pytest.fixture
def background_config_payload():
    return {
        "name": "星空背景",
        "background_type": "color",
        "background_value": "#1a1a2e",
        "is_default": False
    }


# ============================================================================
# 1. 基础端点测试
# ============================================================================

class TestBasicEndpoints:
    """基础端点：健康检查、提供商列表"""

    async def test_health_check(self, client):
        resp = await client.get("/api/v1/crud/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "苏格拉底" in data["message"]

    async def test_list_providers(self, client):
        resp = await client.get("/api/v1/crud/providers")
        assert resp.status_code == 200
        providers = resp.json()
        assert isinstance(providers, list)
        assert len(providers) > 5
        provider_keys = [p["key"] for p in providers]
        assert "openai" in provider_keys
        assert "anthropic" in provider_keys
        for p in providers:
            assert "key" in p
            assert "name" in p
            assert "base_url" in p
            assert "models" in p

    async def test_get_provider_models_without_api_key(self, client):
        resp = await client.get("/api/v1/crud/providers/openai/models")
        assert resp.status_code == 200
        models = resp.json()
        assert isinstance(models, list)
        assert len(models) > 0

    async def test_get_provider_models_invalid_provider(self, client):
        resp = await client.get("/api/v1/crud/providers/nonexistent/models")
        assert resp.status_code == 404


# ============================================================================
# 2. 角色管理完整流程
# ============================================================================

class TestCharacterE2E:
    """角色 CRUD 完整流程：创建 → 列表 → 详情 → 更新 → 删除 → 验证软删除"""

    async def test_full_character_lifecycle(self, client, character_payload):
        # 创建角色
        resp = await client.post("/api/v1/crud/characters", json=character_payload)
        assert resp.status_code == 200
        char = resp.json()
        char_id = char["id"]
        assert char["name"] == character_payload["name"]
        assert char["avatar"] == "👨‍🔬"

        # 列表包含新角色
        resp = await client.get("/api/v1/crud/characters")
        assert resp.status_code == 200
        chars = resp.json()
        assert any(c["id"] == char_id for c in chars)

        # 获取详情
        resp = await client.get(f"/api/v1/crud/characters/{char_id}")
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["id"] == char_id
        assert detail["personality"] == character_payload["personality"]

        # 更新角色
        update = {"name": "爱因斯坦导师（进阶版）", "description": "精通相对论和量子力学"}
        resp = await client.put(f"/api/v1/crud/characters/{char_id}", json=update)
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["name"] == update["name"]
        assert updated["description"] == update["description"]
        assert updated["personality"] == character_payload["personality"]

        # 软删除
        resp = await client.delete(f"/api/v1/crud/characters/{char_id}")
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"

        # 删除后列表不包含
        resp = await client.get("/api/v1/crud/characters")
        assert resp.status_code == 200
        chars = resp.json()
        assert not any(c["id"] == char_id for c in chars)

        # 删除后获取详情应 404
        resp = await client.get(f"/api/v1/crud/characters/{char_id}")
        assert resp.status_code == 404

    async def test_create_character_duplicate_name(self, client, character_payload):
        resp = await client.post("/api/v1/crud/characters", json=character_payload)
        assert resp.status_code == 200
        resp = await client.post("/api/v1/crud/characters", json=character_payload)
        assert resp.status_code == 400

    async def test_create_character_empty_name_fails(self, client):
        resp = await client.post("/api/v1/crud/characters", json={
            "name": "", "personality": "test"
        })
        assert resp.status_code == 422

    async def test_update_nonexistent_character(self, client):
        resp = await client.put("/api/v1/crud/characters/99999", json={"name": "不存在"})
        assert resp.status_code == 404

    async def test_delete_nonexistent_character(self, client):
        resp = await client.delete("/api/v1/crud/characters/99999")
        assert resp.status_code == 404


# ============================================================================
# 3. 教材管理完整流程
# ============================================================================

class TestMaterialE2E:
    """教材 CRUD 完整流程：创建 → 列表 → 详情 → 更新 → 删除"""

    async def test_full_material_lifecycle(self, client, material_payload):
        # 创建教材
        resp = await client.post("/api/v1/crud/materials", json=material_payload)
        assert resp.status_code == 200
        mat = resp.json()
        mat_id = mat["id"]
        assert mat["title"] == material_payload["title"]
        assert mat["content"] == material_payload["content"]

        # 列表包含新教材
        resp = await client.get("/api/v1/crud/materials")
        assert resp.status_code == 200
        mats = resp.json()
        assert any(m["id"] == mat_id for m in mats)

        # 获取详情
        resp = await client.get(f"/api/v1/crud/materials/{mat_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == mat_id

        # 更新教材
        update = {"title": "量子力学进阶", "description": "深入学习量子力学原理"}
        resp = await client.put(f"/api/v1/crud/materials/{mat_id}", json=update)
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["title"] == update["title"]

        # 硬删除
        resp = await client.delete(f"/api/v1/crud/materials/{mat_id}")
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"

        # 删除后获取详情 404
        resp = await client.get(f"/api/v1/crud/materials/{mat_id}")
        assert resp.status_code == 404

    async def test_create_material_empty_title_fails(self, client):
        resp = await client.post("/api/v1/crud/materials", json={"title": ""})
        assert resp.status_code == 422

    async def test_update_nonexistent_material(self, client):
        resp = await client.put("/api/v1/crud/materials/99999", json={"title": "不存在"})
        assert resp.status_code == 404

    async def test_upload_text_file(self, client):
        content = "# 测试教材\n\n这是测试内容。".encode("utf-8")
        resp = await client.post(
            "/api/v1/crud/materials/upload",
            files={"file": ("test.md", content, "text/markdown")}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["filename"] == "test.md"
        assert data["content_url"].endswith(".md")

    async def test_upload_invalid_extension(self, client):
        resp = await client.post(
            "/api/v1/crud/materials/upload",
            files={"file": ("test.exe", b"malware", "application/octet-stream")}
        )
        assert resp.status_code == 400


# ============================================================================
# 4. 模型配置完整流程
# ============================================================================

class TestModelConfigE2E:
    """模型配置 CRUD 完整流程"""

    async def test_full_model_config_lifecycle(self, client, model_config_payload):
        # 创建模型配置
        resp = await client.post("/api/v1/crud/model-configs", json=model_config_payload)
        assert resp.status_code == 200
        cfg = resp.json()
        cfg_id = cfg["id"]
        assert cfg["provider"] == "openai"
        assert cfg["model_name"] == "gpt-4.1"
        assert cfg["is_default"] is True
        assert "api_key" not in cfg  # API key 不应在响应中泄露

        # 列表
        resp = await client.get("/api/v1/crud/model-configs")
        assert resp.status_code == 200
        cfgs = resp.json()
        assert any(c["id"] == cfg_id for c in cfgs)

        # 获取详情
        resp = await client.get(f"/api/v1/crud/model-configs/{cfg_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == cfg_id

        # 创建第二个配置并设为默认 → 第一个自动取消默认
        resp = await client.post("/api/v1/crud/model-configs", json={
            "provider": "anthropic", "model_name": "claude-sonnet-4-20250514",
            "api_key": "sk-ant-test", "is_default": True
        })
        assert resp.status_code == 200
        cfg2_id = resp.json()["id"]

        resp = await client.get(f"/api/v1/crud/model-configs/{cfg_id}")
        assert resp.json()["is_default"] is False
        resp = await client.get(f"/api/v1/crud/model-configs/{cfg2_id}")
        assert resp.json()["is_default"] is True

        # 更新配置
        resp = await client.put(f"/api/v1/crud/model-configs/{cfg2_id}", json={
            "model_name": "claude-opus-4-20250514"
        })
        assert resp.status_code == 200
        assert resp.json()["model_name"] == "claude-opus-4-20250514"

        # 软删除
        resp = await client.delete(f"/api/v1/crud/model-configs/{cfg2_id}")
        assert resp.status_code == 200

    async def test_create_config_invalid_base_url(self, client):
        resp = await client.post("/api/v1/crud/model-configs", json={
            "provider": "openai", "model_name": "gpt-4",
            "base_url": "not-a-url"
        })
        assert resp.status_code == 422

    async def test_create_config_empty_provider_fails(self, client):
        resp = await client.post("/api/v1/crud/model-configs", json={
            "provider": "", "model_name": "gpt-4"
        })
        assert resp.status_code == 422


# ============================================================================
# 5. 背景配置完整流程
# ============================================================================

class TestBackgroundConfigE2E:
    """背景配置 CRUD 完整流程"""

    async def test_background_config_lifecycle(self, client, background_config_payload):
        # 创建
        resp = await client.post("/api/v1/upload/backgrounds", json=background_config_payload)
        assert resp.status_code == 200
        bg = resp.json()
        bg_id = bg["id"]
        assert bg["name"] == background_config_payload["name"]
        assert bg["background_value"] == "#1a1a2e"

        # 列表
        resp = await client.get("/api/v1/upload/backgrounds")
        assert resp.status_code == 200
        bgs = resp.json()
        assert any(b["id"] == bg_id for b in bgs)

        # 默认背景（无默认时返回 fallback）
        resp = await client.get("/api/v1/upload/backgrounds/default")
        assert resp.status_code == 200

        # 详情
        resp = await client.get(f"/api/v1/upload/backgrounds/{bg_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == bg_id

        # 更新
        resp = await client.put(f"/api/v1/upload/backgrounds/{bg_id}", json={
            "name": "深空背景", "background_value": "#0d0d2b"
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "深空背景"

        # 删除
        resp = await client.delete(f"/api/v1/upload/backgrounds/{bg_id}")
        assert resp.status_code == 200

    async def test_get_nonexistent_background(self, client):
        resp = await client.get("/api/v1/upload/backgrounds/99999")
        assert resp.status_code == 404


# ============================================================================
# 6. 对话会话完整生命周期
# ============================================================================

class TestConversationE2E:
    """对话 CRUD 完整流程：创建 → 列表 → 详情（含消息）→ 更新 → 删除（级联）"""

    async def test_conversation_lifecycle(
        self, client, character_payload, material_payload, model_config_payload
    ):
        # 创建前置数据
        r = await client.post("/api/v1/crud/characters", json=character_payload)
        char_id = r.json()["id"]

        r = await client.post("/api/v1/crud/materials", json=material_payload)
        mat_id = r.json()["id"]

        await client.post("/api/v1/crud/model-configs", json=model_config_payload)

        # 创建对话
        conv_data = {
            "title": "量子力学讨论",
            "character_id": char_id,
            "material_id": mat_id,
            "teaching_mode": "socratic"
        }
        resp = await client.post("/api/v1/crud/conversations", json=conv_data)
        assert resp.status_code == 200
        conv = resp.json()
        conv_id = conv["id"]
        assert conv["title"] == "量子力学讨论"
        assert conv["character_id"] == char_id
        assert conv["material_id"] == mat_id

        # 列表（含角色关联信息）
        resp = await client.get("/api/v1/crud/conversations")
        assert resp.status_code == 200
        convs = resp.json()
        assert any(c["id"] == conv_id for c in convs)

        # 详情（含消息列表、角色、教材）
        resp = await client.get(f"/api/v1/crud/conversations/{conv_id}")
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["id"] == conv_id
        assert detail["character"] is not None
        assert detail["character"]["name"] == character_payload["name"]
        assert detail["material"] is not None
        assert detail["messages"] == []

        # 更新对话
        resp = await client.put(f"/api/v1/crud/conversations/{conv_id}", json={
            "title": "量子力学深入探讨", "teaching_mode": "mixed"
        })
        assert resp.status_code == 200
        assert resp.json()["title"] == "量子力学深入探讨"

        # 删除对话（级联删除消息）
        resp = await client.delete(f"/api/v1/crud/conversations/{conv_id}")
        assert resp.status_code == 200

        # 删除后获取详情 404
        resp = await client.get(f"/api/v1/crud/conversations/{conv_id}")
        assert resp.status_code == 404

    async def test_create_conversation_invalid_mode(self, client, character_payload):
        r = await client.post("/api/v1/crud/characters", json=character_payload)
        char_id = r.json()["id"]
        resp = await client.post("/api/v1/crud/conversations", json={
            "character_id": char_id, "teaching_mode": "invalid_mode"
        })
        assert resp.status_code == 422

    async def test_create_conversation_without_character(self, client):
        resp = await client.post("/api/v1/crud/conversations", json={
            "character_id": 99999, "teaching_mode": "socratic"
        })
        assert resp.status_code == 400


# ============================================================================
# 7. 完整苏格拉底教学会话（模拟 LLM）
# ============================================================================

class TestTutoringSessionE2E:
    """模拟完整的苏格拉底教学流程：创建资源 → 开启对话 → 多轮聊天 → 验证历史"""

    MOCK_RESPONSE = "这是一个很好的问题！让我们用苏格拉底式的方法来思考。首先，你认为'学习'的本质是什么？"

    async def test_full_tutoring_session(self, client, character_payload, material_payload, model_config_payload, mocker):
        char_r = await client.post("/api/v1/crud/characters", json=character_payload)
        char_id = char_r.json()["id"]

        mat_r = await client.post("/api/v1/crud/materials", json=material_payload)
        mat_id = mat_r.json()["id"]

        cfg_r = await client.post("/api/v1/crud/model-configs", json=model_config_payload)
        cfg_id = cfg_r.json()["id"]

        conv_r = await client.post("/api/v1/crud/conversations", json={
            "title": "苏格拉底式物理教学",
            "character_id": char_id,
            "material_id": mat_id,
            "teaching_mode": "socratic"
        })
        conv_id = conv_r.json()["id"]

        # Mock LLM 调用以返回预设回复
        mock_chat = mocker.patch(
            "app.services.chat_service.LLMProvider.chat",
            return_value=self.MOCK_RESPONSE
        )

        # 第一轮聊天
        resp = await client.post(
            f"/api/v1/chat/{conv_id}",
            json={"content": "什么是量子力学？"},
            params={"model_config_id": cfg_id}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert data["response"] == self.MOCK_RESPONSE
        mock_chat.assert_called_once()

        # 验证消息已被保存
        detail_r = await client.get(f"/api/v1/crud/conversations/{conv_id}")
        messages = detail_r.json()["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "什么是量子力学？"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == self.MOCK_RESPONSE

        # 第二轮聊天
        mock_chat.return_value = "很好的观察！让我们深入探讨波粒二象性的概念。"
        resp = await client.post(
            f"/api/v1/chat/{conv_id}",
            json={"content": "我听说过薛定谔的猫，能解释一下吗？"},
            params={"model_config_id": cfg_id}
        )
        assert resp.status_code == 200

        # 验证共 4 条消息
        detail_r = await client.get(f"/api/v1/crud/conversations/{conv_id}")
        messages = detail_r.json()["messages"]
        assert len(messages) == 4

    async def test_chat_without_model_config(self, client, character_payload, material_payload, model_config_payload, mocker):
        char_r = await client.post("/api/v1/crud/characters", json=character_payload)
        mat_r = await client.post("/api/v1/crud/materials", json=material_payload)
        await client.post("/api/v1/crud/model-configs", json=model_config_payload)

        conv_r = await client.post("/api/v1/crud/conversations", json={
            "title": "测试对话", "character_id": char_r.json()["id"],
            "material_id": mat_r.json()["id"], "teaching_mode": "socratic"
        })
        conv_id = conv_r.json()["id"]

        mock_chat = mocker.patch(
            "app.services.chat_service.LLMProvider.chat",
            return_value="使用默认配置的回复。"
        )

        resp = await client.post(
            f"/api/v1/chat/{conv_id}",
            json={"content": "不使用指定模型配置"}
        )
        assert resp.status_code == 200
        assert resp.json()["response"] == "使用默认配置的回复。"

    async def test_chat_nonexistent_conversation(self, client, model_config_payload):
        await client.post("/api/v1/crud/model-configs", json=model_config_payload)
        resp = await client.post("/api/v1/chat/99999", json={"content": "Hello"})
        assert resp.status_code == 400

    async def test_chat_stream_response(self, client, character_payload, material_payload, model_config_payload, mocker):
        char_r = await client.post("/api/v1/crud/characters", json=character_payload)
        mat_r = await client.post("/api/v1/crud/materials", json=material_payload)
        await client.post("/api/v1/crud/model-configs", json=model_config_payload)

        conv_r = await client.post("/api/v1/crud/conversations", json={
            "title": "流式对话", "character_id": char_r.json()["id"],
            "material_id": mat_r.json()["id"], "teaching_mode": "socratic"
        })
        conv_id = conv_r.json()["id"]

        async def mock_stream(messages):
            for c in "流式":
                yield c
            for c in "回复":
                yield c

        mocker.patch(
            "app.services.chat_service.LLMProvider.chat_stream",
            side_effect=mock_stream
        )

        resp = await client.post(
            f"/api/v1/chat/{conv_id}/stream",
            json={"content": "测试流式"}
        )
        assert resp.status_code == 200
        body = resp.text
        assert "data:" in body
        assert "[DONE]" in body


# ============================================================================
# 8. 复合端到端场景
# ============================================================================

class TestCompositeScenarios:
    """跨越多个实体的复合场景测试"""

    async def test_create_study_session_and_cleanup(
        self, client, character_payload, material_payload, model_config_payload
    ):
        """模拟前端完整操作流程：创建学习资源 → 开始学习 → 结束并清理"""
        r1 = await client.post("/api/v1/crud/characters", json=character_payload)
        char_id = r1.json()["id"]

        r2 = await client.post("/api/v1/crud/materials", json=material_payload)
        mat_id = r2.json()["id"]

        r3 = await client.post("/api/v1/crud/model-configs", json=model_config_payload)

        conv_resp = await client.post("/api/v1/crud/conversations", json={
            "title": "完整学习会话", "character_id": char_id,
            "material_id": mat_id, "teaching_mode": "socratic"
        })
        conv_id = conv_resp.json()["id"]

        conversations = (await client.get("/api/v1/crud/conversations")).json()
        assert any(c["id"] == conv_id for c in conversations)

        await client.delete(f"/api/v1/crud/conversations/{conv_id}")
        await client.delete(f"/api/v1/crud/materials/{mat_id}")
        await client.delete(f"/api/v1/crud/characters/{char_id}")

    async def test_multiple_characters_and_materials(self, client):
        """创建多个角色和教材，验证列表和独立性"""
        chars = ["数学导师", "物理导师", "化学导师"]
        char_ids = []
        for name in chars:
            r = await client.post("/api/v1/crud/characters", json={
                "name": name, "personality": "专业严谨", "avatar_type": "emoji"
            })
            char_ids.append(r.json()["id"])

        mats = ["代数基础", "力学原理", "有机化学"]
        mat_ids = []
        for title in mats:
            r = await client.post("/api/v1/crud/materials", json={
                "title": title, "content": f"{title}的教学内容"
            })
            mat_ids.append(r.json()["id"])

        all_chars = (await client.get("/api/v1/crud/characters")).json()
        assert len(all_chars) >= 3
        for cid in char_ids:
            assert any(c["id"] == cid for c in all_chars)

        all_mats = (await client.get("/api/v1/crud/materials")).json()
        assert len(all_mats) >= 3
        for mid in mat_ids:
            assert any(m["id"] == mid for m in all_mats)

    async def test_update_and_verify_cascade(self, client, character_payload, material_payload, model_config_payload):
        """测试更新操作后数据一致性"""
        r = await client.post("/api/v1/crud/characters", json=character_payload)
        char_id = r.json()["id"]

        r = await client.post("/api/v1/crud/materials", json=material_payload)
        mat_id = r.json()["id"]

        await client.post("/api/v1/crud/model-configs", json=model_config_payload)

        r = await client.post("/api/v1/crud/conversations", json={
            "title": "原始标题", "character_id": char_id,
            "material_id": mat_id, "teaching_mode": "socratic"
        })
        conv_id = r.json()["id"]

        # 更新教材内容不影响已创建的对话
        await client.put(f"/api/v1/crud/materials/{mat_id}", json={
            "title": "更新后的教材标题"
        })

        # 对话中的 material 应反映最新内容
        conv_detail = (await client.get(f"/api/v1/crud/conversations/{conv_id}")).json()
        assert conv_detail["material"]["title"] == "更新后的教材标题"
