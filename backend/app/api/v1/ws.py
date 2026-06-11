import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.logging_config import get_logger
from app.engines.ui_orchestrator import UIOrchestrator

logger = get_logger(__name__)

router = APIRouter()

_narrative_engine = None
_ui_orchestrator = UIOrchestrator()


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

            elif msg_type == "time.advance":
                days = payload.get("days", 1)
                engine = get_narrative_engine()
                if engine:
                    result = engine.world.advance_time(days)
                    await engine.state_manager.update("time_advance", {
                        "current_day": result["current_day"],
                        "narrative_phase": result["narrative_phase"],
                    })
                    await websocket.send_text(json.dumps({
                        "type": "time.advanced",
                        "payload": result,
                    }, ensure_ascii=False))

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
                    if model_config_id is not None:
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
                    logger.error(f"Chat error: {e}", exc_info=True)
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

            elif msg_type == "action.choose":
                option_id = payload.get("option_id", "")
                event_id = payload.get("event_id", "")
                engine = get_narrative_engine()
                if engine:
                    await engine.state_manager.update("narrative_choice", {
                        "flag_key": f"choice_{event_id}",
                        "flag_value": option_id,
                    })
                    await websocket.send_text(json.dumps({
                        "type": "event.resolved",
                        "payload": {"event_id": event_id, "chosen_option": option_id},
                    }, ensure_ascii=False))

            elif msg_type == "assessment.generate":
                point_id = payload.get("point_id", "")
                character_id = payload.get("character_id", "")
                engine = get_narrative_engine()
                if engine and engine.assessment:
                    result = await engine.generate_quiz(
                        point_id=point_id,
                        character_id=character_id,
                    )
                    if "error" in result:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "content": result["error"],
                        }))
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "assessment.quiz",
                            "payload": result,
                        }, ensure_ascii=False))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "content": "AssessmentEngine not initialized",
                    }))

            elif msg_type == "assessment.answer":
                point_id = payload.get("point_id", "")
                character_id = payload.get("character_id", "")
                answers = payload.get("answers", [])
                conversation_id = payload.get("conversation_id", 0)
                engine = get_narrative_engine()
                if engine and engine.assessment:
                    result = await engine.handle_assessment_answer(
                        conversation_id=conversation_id,
                        point_id=point_id,
                        answers=answers,
                        character_id=character_id,
                    )
                    await websocket.send_text(json.dumps({
                        "type": "assessment.result",
                        "payload": result,
                    }, ensure_ascii=False))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "content": "AssessmentEngine not initialized",
                    }))

            elif msg_type == "syllabus.confirm":
                material_id = payload.get("material_id")
                if material_id:
                    from app.tasks.material_pipeline import process_material
                    from app.repositories.unit_of_work import UnitOfWork
                    async with UnitOfWork() as uow:
                        material = await uow.materials.get_by_id(material_id)
                        if material:
                            await uow.materials.update(material, {
                                "status": "ready",
                                "review_status": "approved",
                            })
                    await websocket.send_text(json.dumps({
                        "type": "material.status_changed",
                        "payload": {
                            "material_id": material_id,
                            "status": "ready",
                            "progress": 100,
                            "progress_message": "结构化教学已开启",
                            "capabilities": {
                                "free_chat": True,
                                "structured_mode": True,
                                "exercises": True,
                                "progress_tracking": True,
                            },
                        },
                    }, ensure_ascii=False))

            elif msg_type == "syllabus.activate":
                material_id = payload.get("material_id")
                if not material_id:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "content": "缺少 material_id",
                    }))
                    continue
                engine = get_narrative_engine()
                if engine:
                    result = await engine.activate_syllabus(material_id)
                    if "error" in result:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "content": result["error"],
                        }))
                    else:
                        snapshot = await engine.get_full_snapshot()
                        await websocket.send_text(json.dumps({
                            "type": "syllabus.activated",
                            "payload": result,
                        }, ensure_ascii=False))
                        await websocket.send_text(json.dumps({
                            "type": "state.full",
                            "payload": snapshot,
                        }, ensure_ascii=False))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "content": "叙事引擎未初始化",
                    }))

            elif msg_type == "syllabus.reject":
                material_id = payload.get("material_id")
                if material_id:
                    from app.repositories.unit_of_work import UnitOfWork
                    async with UnitOfWork() as uow:
                        material = await uow.materials.get_by_id(material_id)
                        if material:
                            await uow.materials.update(material, {
                                "status": "indexed",
                                "review_status": "rejected",
                            })
                    await websocket.send_text(json.dumps({
                        "type": "material.status_changed",
                        "payload": {
                            "material_id": material_id,
                            "status": "indexed",
                            "progress": 100,
                            "progress_message": "大纲已拒绝，使用自由对话模式",
                            "capabilities": {
                                "free_chat": True,
                                "structured_mode": False,
                                "exercises": False,
                                "progress_tracking": False,
                            },
                        },
                    }, ensure_ascii=False))

            elif msg_type == "ui.interact":
                component_id = payload.get("component_id", "")
                action = payload.get("action", "")
                value = payload.get("value", "")
                logger.info(f"UI interact: component={component_id}, action={action}")

            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": f"未知的消息类型: {msg_type}",
                }))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception:
            pass