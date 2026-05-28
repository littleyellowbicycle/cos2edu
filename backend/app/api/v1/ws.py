import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()

_narrative_engine = None


def set_narrative_engine(engine):
    global _narrative_engine
    _narrative_engine = engine


def get_narrative_engine():
    return _narrative_engine


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    model_config_id: Optional[int] = Query(None),
):
    await websocket.accept()
    client_id = id(websocket)
    logger.info(f"WebSocket connected: {client_id}")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "content": "无效的JSON格式"}))
                continue

            msg_type = msg.get("type", "")
            payload = msg.get("payload", {})

            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

            elif msg_type == "state.sync":
                engine = get_narrative_engine()
                if engine:
                    snapshot = await engine.get_full_snapshot()
                    await websocket.send_text(json.dumps({
                        "type": "state.full",
                        "payload": snapshot,
                    }, ensure_ascii=False))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "state.full",
                        "payload": {},
                    }))

            elif msg_type == "chat.send":
                content = payload.get("content", "")
                conversation_id = payload.get("conversation_id")
                character_id = payload.get("character_id", "")

                if not conversation_id or not content:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "content": "缺少 conversation_id 或 content",
                    }))
                    continue

                engine = get_narrative_engine()
                if not engine:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "content": "叙事引擎未初始化",
                    }))
                    continue

                try:
                    from app.services import ModelConfigService
                    model_config = None
                    if model_config_id:
                        model_config = await ModelConfigService.get_by_id(model_config_id)
                    else:
                        model_config = await ModelConfigService.get_default()

                    async for event_str in engine.handle_chat_message(
                        conversation_id=conversation_id,
                        user_message=content,
                        character_id=character_id,
                        model_config=model_config,
                    ):
                        await websocket.send_text(event_str)

                except Exception as e:
                    logger.error(f"Chat error: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "content": str(e),
                    }))

            elif msg_type == "scene.switch":
                scene_id = payload.get("scene_id", "")
                engine = get_narrative_engine()
                if engine:
                    scene = engine.world.switch_scene(scene_id)
                    await engine.state_manager.update("scene_change", {
                        "scene_id": scene_id,
                    })
                    await websocket.send_text(json.dumps({
                        "type": "scene.change",
                        "payload": {
                            "scene_id": scene.id,
                            "scene_name": scene.name,
                            "description": scene.description,
                            "allowed_actions": scene.allowed_actions,
                        },
                    }, ensure_ascii=False))

            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": f"未知的消息类型: {msg_type}",
                }))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception:
            pass