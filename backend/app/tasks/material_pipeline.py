import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable, Awaitable

from app.parsers.parser_registry import parser_registry
from app.parsers.base import ParseResult, ParseErrorCode
from app.services.rag_service import get_rag_service
from app.tasks.quality_check import validate_outline, QualityCheckResult
from app.core.logging_config import get_logger

logger = get_logger(__name__)


# Statuses considered "stuck" when the process died mid-flight; repair-stuck scans these.
STUCK_STATUSES = ("parsing",)


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
    quality_reasons: list[str] = field(default_factory=list)


_task_registry: dict[int, MaterialTask] = {}


async def process_material(
    material_id: int,
    file_path: str,
    uow_factory,
    ws_notify: Optional[Callable] = None,
    text: Optional[str] = None,
) -> None:
    """Process a material through the full pipeline:
    parse -> index -> outline -> quality_check -> pending_review

    If `text` is provided, skips file parsing and uses it directly.
    """
    task = MaterialTask(material_id=material_id, started_at=datetime.now(timezone.utc))
    _task_registry[material_id] = task

    try:
        result: Optional[ParseResult] = None

        if text is not None:
            # Content already available — skip parsing phase
            result = ParseResult(success=True, text=text, char_count=len(text))
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
            if material is None:
                # Material vanished mid-flight (deleted) — fail loudly instead of
                # silently progressing against a detached/ghost row.
                raise MaterialPipelineError(
                    "MATERIAL_NOT_FOUND",
                    f"教材 {material_id} 在索引阶段不存在，可能已被删除",
                )
            await uow.materials.update(material, {
                "content": result.text[:500000],
                "page_count": getattr(result, 'page_count', None) or None,
                # `getattr`'s default only applies when the attribute is missing;
                # the text-path ParseResult carries char_count=0, so fall back
                # to len(text) when the parser did not report a count.
                "char_count": getattr(result, 'char_count', 0) or len(result.text),
                "status": "indexed",
            })
        task.status = "indexed"
        task.progress_message = "索引建立完成，可以开始自由对话"
        task.progress = 60
        await _notify(ws_notify, material_id, task)

        # Phase 2.5: Index text into RAG (best-effort; never blocks the pipeline)
        try:
            rag = get_rag_service()
            if getattr(rag, "_initialized", False) and result.text:
                num_chunks = rag.index_text(result.text, source_id=str(material_id))
                logger.info(f"RAG indexed {num_chunks} chunks for material {material_id}")
        except Exception as e:
            logger.warning(f"RAG indexing failed for material {material_id}: {e}")

        # Phase 3: Outline (LLM auto-generate syllabus)
        task.status = "outlining"
        task.progress_message = "正在分析章节结构..."
        task.progress = 70
        await _notify(ws_notify, material_id, task)

        try:
            outline = await _generate_outline(result.text, uow_factory)
        except Exception as outline_err:
            logger.warning(f"Outline generation failed for material {material_id}: {outline_err}")
            outline = None

        if not outline:
            # Outline generation failed: keep the material indexed for free chat.
            task.status = "indexed"
            task.progress = 100
            task.progress_message = "大纲生成失败，可使用自由对话模式"
            async with uow_factory() as uow:
                material = await uow.materials.get_by_id(material_id)
                if material:
                    await uow.materials.update(material, {"status": "indexed"})
            await _notify(ws_notify, material_id, task)
            return

        # Phase 4: Quality check (outline validation before human review)
        task.status = "quality_check"
        task.progress_message = "正在校验大纲质量..."
        task.progress = 85
        await _notify(ws_notify, material_id, task)

        try:
            check: QualityCheckResult = validate_outline(outline)
        except Exception as vc_err:
            # 校验器内部异常属于防御性降级：不让整条管线崩到 failed，
            # 物料退回到 indexed（自由对话可用），由人工后续处理。
            logger.error(f"Quality check crashed for material {material_id}: {vc_err}", exc_info=True)
            task.status = "indexed"
            task.progress = 100
            task.progress_message = "大纲质量校验异常，已降级为自由对话模式"
            async with uow_factory() as uow:
                material = await uow.materials.get_by_id(material_id)
                if material:
                    await uow.materials.update(material, {"status": "indexed"})
            await _notify(ws_notify, material_id, task)
            return

        if not check.passed:
            task.status = "review_rejected"
            task.progress = 100
            task.progress_message = "大纲未通过质量校验"
            task.error_code = check.error_code or "QUALITY_CHECK_FAILED"
            task.error_message = "; ".join(check.reasons)
            task.quality_reasons = check.reasons
            task.completed_at = datetime.now(timezone.utc)

            async with uow_factory() as uow:
                material = await uow.materials.get_by_id(material_id)
                if material:
                    await uow.materials.update(material, {
                        "status": "review_rejected",
                        "review_status": "rejected",
                        "error_code": task.error_code,
                    })

            await _notify(ws_notify, material_id, task)
            await _notify_quality_rejected(ws_notify, material_id, check)
            return

        # Phase 5: Outline passed review gate -> pending_review
        task.progress = 90
        task.progress_message = "大纲生成完成，等待确认"
        task.progress = 100

        async with uow_factory() as uow:
            # Re-fetch inside THIS session: the material object from an earlier
            # (closed) session is detached and updates on it are not persisted.
            material = await uow.materials.get_by_id(material_id)
            if material is None:
                raise MaterialPipelineError(
                    "MATERIAL_NOT_FOUND",
                    f"教材 {material_id} 在大纲阶段不存在，可能已被删除",
                )
            await uow.materials.update(material, {
                "status": "pending_review",
                "review_status": "pending",
            })

            syllabus_data = {
                "name": outline.get("name", "自动生成大纲"),
                "total_days": outline.get("total_days", 60),
                "content": outline,
                "generated_by": "llm",
                "review_status": "pending",
            }
            # 重复触发（手动重跑 / repair-stuck）时更新已有大纲，避免同一物料
            # 堆积多条 syllabus，导致 get_by_material_id 命中多行。
            existing_syllabus = await uow.syllabuses.get_by_material_id(material_id)
            if existing_syllabus:
                await uow.syllabuses.update(existing_syllabus, syllabus_data)
            else:
                await uow.syllabuses.create({**syllabus_data, "material_id": material_id})

        task.status = "pending_review"
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


async def _generate_outline(text_content: str, uow_factory=None) -> Optional[dict]:
    """Use LLM to generate a structured outline from text content

    Raises exceptions with descriptive messages instead of returning None,
    so callers can report the specific cause of failure.
    `uow_factory` is injected so tests can bind to an in-memory session;
    it defaults to the production UnitOfWork when omitted.
    """
    from app.services.chat_service import LLMProvider
    from app.repositories.unit_of_work import UnitOfWork

    factory = uow_factory or UnitOfWork

    async with factory() as uow:
        config_obj = await uow.model_configs.get_default()
        if not config_obj:
            raise ValueError("未配置默认AI模型，请前往设置页面配置模型和API Key")

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

    if not response:
        raise ValueError("AI返回了空内容，请检查模型配置或重试")

    import re
    response = re.sub(r'<think\b.*?</think\s*>?', '', response, flags=re.DOTALL | re.IGNORECASE)
    response = response.strip()

    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    response = response.strip()

    json_match = re.search(r'\{[\s\S]*\}', response)
    if not json_match:
        logger.error(f"No JSON object found in LLM response. Response preview: {response[:500]}")
        raise ValueError("AI返回的内容中未找到有效JSON，请重试或更换模型")

    json_str = json_match.group(0)

    try:
        outline = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM outline response as JSON: {e}, response preview: {json_str[:500]}")
        raise ValueError(f"AI返回的内容无法解析为JSON，请重试或更换模型")

    logger.info(f"Generated outline: {outline.get('name', 'unknown')} with {len(outline.get('modules', []))} modules")
    return outline


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


async def repair_stuck_materials(
    uow_factory,
    ws_notify: Optional[Callable] = None,
    reprocess: Optional[Callable[..., Awaitable[None]]] = None,
    schedule: Optional[Callable[[Awaitable], None]] = None,
) -> dict:
    """Re-process materials stuck in a transitional status after a crash.

    - Materials that already carry `content` are reprocessed in-place via the
      text path (no file re-read), scheduled through `schedule` (defaults to
      `asyncio.create_task`; tests may pass a collector to await directly).
    - Materials without content are marked `failed` instead of hanging forever
      in the stuck status (they cannot be repaired without the source file).

    Returns a summary dict: {"repaired": [...ids], "failed": [...ids], "stuck": [...]}
    """
    reprocess_fn = reprocess or process_material
    schedule_fn = schedule or asyncio.create_task
    repaired: list[int] = []
    failed: list[int] = []
    stuck_ids: list[int] = []

    async with uow_factory() as uow:
        stuck_materials: list = []
        for status in STUCK_STATUSES:
            stuck_materials.extend(await uow.materials.get_by_status(status))

    for material in stuck_materials:
        stuck_ids.append(material.id)
        if material.content:
            schedule_fn(reprocess_fn(
                material_id=material.id,
                file_path="",
                uow_factory=uow_factory,
                ws_notify=ws_notify,
                text=material.content,
            ))
            repaired.append(material.id)
        else:
            await _update_material_status(
                uow_factory, material.id, "failed", error_code="STUCK_NO_CONTENT"
            )
            failed.append(material.id)

    logger.info(f"repair-stuck: repaired={repaired}, failed={failed}")
    return {"repaired": repaired, "failed": failed, "stuck": stuck_ids}


def _capabilities_for(status: str) -> dict:
    return {
        "free_chat": status in ("indexed", "outlining", "quality_check", "pending_review",
                                "review_rejected"),
        "structured_mode": status == "ready",
        "exercises": status == "ready",
        "progress_tracking": status == "ready",
    }


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
                    "capabilities": _capabilities_for(task.status),
                },
            })
        except Exception as e:
            logger.error(f"WebSocket notify failed: {e}")


async def _notify_quality_rejected(
    ws_notify: Optional[Callable],
    material_id: int,
    check: QualityCheckResult,
) -> None:
    if ws_notify:
        try:
            ws_notify({
                "type": "material.quality_rejected",
                "payload": {
                    "material_id": material_id,
                    "status": "review_rejected",
                    "reasons": check.reasons,
                    "error_code": check.error_code,
                    "progress_message": "大纲未通过质量校验",
                },
            })
        except Exception as e:
            logger.error(f"WebSocket quality-rejected notify failed: {e}")


def get_task_status(material_id: int) -> Optional[MaterialTask]:
    return _task_registry.get(material_id)
