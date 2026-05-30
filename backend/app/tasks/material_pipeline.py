import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable

from app.parsers.parser_registry import parser_registry
from app.parsers.base import ParseResult, ParseErrorCode
from app.services.rag_service import get_rag_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class MaterialPipelineError(Exception):
    def __init__(self, error_code: str, message: str, suggestion: str = ""):
        self.error_code = error_code
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)


@dataclass
class MaterialTask:
    material_id: int
    status: str = "parsing"
    progress: float = 0.0
    progress_message: str = ""
    error_code: Optional[str] = None
    error_message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parse_result: Optional[ParseResult] = None


_task_registry: dict[int, MaterialTask] = {}


async def process_material(
    material_id: int,
    file_path: str,
    uow_factory,
    ws_notify: Optional[Callable] = None,
    text: Optional[str] = None,
) -> None:
    """Process a material through the full pipeline: parse -> index -> outline -> pending_review
    
    If `text` is provided, skips file parsing and uses it directly.
    """
    task = MaterialTask(material_id=material_id, started_at=datetime.now(timezone.utc))
    _task_registry[material_id] = task

    try:
        result: Optional[ParseResult] = None

        if text is not None:
            # Content already available — skip parsing phase
            from app.parsers.base import ParseResult
            result = ParseResult(success=True, text=text)
            task.progress = 30
            task.progress_message = "内容已就绪"
        else:
            # Phase 1: Parse
            task.status = "parsing"
            task.progress_message = "正在解析文件..."
            task.progress = 10
            await _notify(ws_notify, material_id, task)

            result = await parser_registry.parse(file_path)

            if not result.success:
                task.status = "failed"
                task.error_code = result.error_code
                task.error_message = result.error_message
                task.completed_at = datetime.now(timezone.utc)
                await _update_material_status(uow_factory, material_id, "failed",
                                              error_code=result.error_code)
                await _notify(ws_notify, material_id, task)
                return

            task.parse_result = result
            task.progress = 30
            task.progress_message = "文件解析完成"

        # Phase 2: Index (store text content)
        task.status = "indexing"
        task.progress_message = "正在建立内容索引..."
        task.progress = 50
        await _notify(ws_notify, material_id, task)

        async with uow_factory() as uow:
            material = await uow.materials.get_by_id(material_id)
            if material:
                await uow.materials.update(material, {
                    "content": result.text[:500000],
                    "page_count": getattr(result, 'page_count', None),
                    "char_count": getattr(result, 'char_count', len(result.text)),
                    "status": "indexed",
                })
        task.status = "indexed"
        task.progress_message = "索引建立完成，可以开始自由对话"
        task.progress = 60
        await _notify(ws_notify, material_id, task)

        # Phase 2.5: Index text into RAG
        try:
            rag = get_rag_service()
            if rag._initialized and result.text:
                num_chunks = rag.index_text(result.text, source_id=str(material_id))
                logger.info(f"RAG indexed {num_chunks} chunks for material {material_id}")
        except Exception as e:
            logger.warning(f"RAG indexing failed for material {material_id}: {e}")

        # Phase 3: Outline (LLM auto-generate syllabus)
        task.status = "outlining"
        task.progress_message = "正在分析章节结构..."
        task.progress = 70
        await _notify(ws_notify, material_id, task)

        outline = await _generate_outline(result.text, uow_factory)

        if outline:
            task.progress = 90
            task.progress_message = "大纲生成完成，等待确认"
            task.progress = 100

            async with uow_factory() as uow:
                await uow.materials.update(material, {
                    "status": "pending_review",
                    "review_status": "pending",
                })

                from models.syllabus import Syllabus
                syllabus_data = {
                    "name": outline.get("name", "自动生成大纲"),
                    "total_days": outline.get("total_days", 60),
                    "content": outline,
                    "generated_by": "llm",
                    "review_status": "pending",
                }
                await uow.syllabuses.create(syllabus_data)

            task.status = "pending_review"
            await _notify(ws_notify, material_id, task)
        else:
            task.status = "indexed"
            task.progress = 100
            task.progress_message = "大纲生成失败，可使用自由对话模式"
            async with uow_factory() as uow:
                await uow.materials.update(await uow.materials.get_by_id(material_id), {
                    "status": "indexed",
                })
            await _notify(ws_notify, material_id, task)

    except Exception as e:
        logger.error(f"Material pipeline error for {material_id}: {e}", exc_info=True)
        task.status = "failed"
        task.error_code = ParseErrorCode.UNKNOWN_ERROR
        task.error_message = str(e)
        task.completed_at = datetime.now(timezone.utc)
        try:
            await _update_material_status(uow_factory, material_id, "failed",
                                          error_code="UNKNOWN_ERROR")
        except Exception:
            pass
        await _notify(ws_notify, material_id, task)


async def _generate_outline(text_content: str, uow_factory) -> Optional[dict]:
    """Use LLM to generate a structured outline from text content"""
    try:
        from app.services.chat_service import LLMProvider
        from app.repositories.unit_of_work import UnitOfWork

        async with UnitOfWork() as uow:
            config_obj = await uow.model_configs.get_default()
            if not config_obj:
                logger.warning("No default model config for outline generation")
                return None

            config_dict = {
                "provider": config_obj.provider,
                "model_name": config_obj.model_name,
                "api_key": config_obj.api_key,
                "base_url": config_obj.base_url,
                "group_id": getattr(config_obj, "group_id", None),
            }

        llm = LLMProvider(config_dict)

        truncated = text_content[:8000]

        prompt = f"""你是一位专业的课程设计师。请分析以下教材内容，为其设计一份结构化的学习大纲。

教材内容片段：
{truncated}

请严格按以下JSON格式输出（不要输出其他内容）：
{{
  "name": "教材名称",
  "total_days": 60,
  "phases": [
    {{
      "name": "阶段名称",
      "days": [1, 20],
      "modules": ["模块1", "模块2"]
    }}
  ],
  "modules": [
    {{
      "id": "模块ID(英文下划线)",
      "name": "模块名称",
      "order": 1,
      "estimated_hours": 16,
      "prerequisites": [],
      "knowledge_points": [
        {{
          "id": "知识点ID(英文下划线)",
          "name": "知识点名称",
          "difficulty": 1,
          "key_concepts": ["概念1", "概念2"],
          "prerequisites": []
        }}
      ]
    }}
  ]
}}"""

        messages = [{"role": "user", "content": prompt}]
        response = await llm.chat(messages)

        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        outline = json.loads(response)
        logger.info(f"Generated outline: {outline.get('name', 'unknown')} with {len(outline.get('modules', []))} modules")
        return outline

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM outline response as JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Outline generation failed: {e}")
        return None


async def _update_material_status(uow_factory, material_id: int, status: str,
                                   error_code: str = None) -> None:
    try:
        async with uow_factory() as uow:
            material = await uow.materials.get_by_id(material_id)
            if material:
                update_data = {"status": status}
                if error_code:
                    update_data["error_code"] = error_code
                await uow.materials.update(material, update_data)
    except Exception as e:
        logger.error(f"Failed to update material status: {e}")


async def _notify(ws_notify: Optional[Callable], material_id: int, task: MaterialTask) -> None:
    if ws_notify:
        try:
            ws_notify({
                "type": "material.status_changed",
                "payload": {
                    "material_id": material_id,
                    "status": task.status,
                    "progress": task.progress,
                    "progress_message": task.progress_message,
                    "capabilities": {
                        "free_chat": task.status in ("indexed", "outlining", "pending_review"),
                        "structured_mode": task.status == "ready",
                        "exercises": task.status == "ready",
                        "progress_tracking": task.status == "ready",
                    },
                },
            })
        except Exception as e:
            logger.error(f"WebSocket notify failed: {e}")


def get_task_status(material_id: int) -> Optional[MaterialTask]:
    return _task_registry.get(material_id)