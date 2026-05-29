from typing import Optional
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel

from app.core.limiter import limiter
from app.core.logging_config import get_logger
from app.repositories.unit_of_work import UnitOfWork
from app.tasks.material_pipeline import process_material, get_task_status
from app.parsers.parser_registry import parser_registry
from app.parsers.base import ParseErrorCode
from app.schemas.enums import MaterialStatus

logger = get_logger(__name__)

router = APIRouter()


class MaterialStatusResponse(BaseModel):
    status: str
    progress: float = 0
    progress_message: str = ""
    error_code: Optional[str] = None
    error_message: str = ""
    capabilities: dict = {}
    timeline: Optional[dict] = None
    syllabus_preview: Optional[dict] = None


class SyllabusConfirmRequest(BaseModel):
    material_id: int


class SyllabusEditRequest(BaseModel):
    material_id: int
    name: Optional[str] = None
    total_days: Optional[int] = None
    content: Optional[dict] = None


class AssessmentGenerateRequest(BaseModel):
    point_id: str
    character_id: str = ""


@router.get("/materials/{material_id}/status", response_model=MaterialStatusResponse)
@limiter.limit("60/minute")
async def get_material_status(request: Request, material_id: int):
    async with UnitOfWork() as uow:
        material = await uow.materials.get_by_id(material_id)
        if not material:
            raise HTTPException(status_code=404, detail="教材不存在")

    task = get_task_status(material_id)

    status = material.status if material.status else "parsing"
    capabilities = {
        "free_chat": status in ("indexed", "outlining", "pending_review"),
        "structured_mode": status == "ready",
        "exercises": status == "ready",
        "progress_tracking": status == "ready",
    }

    response = MaterialStatusResponse(
        status=status,
        progress=task.progress if task else (100 if status in ("indexed", "pending_review", "ready") else 0),
        progress_message=task.progress_message if task else "",
        error_code=material.error_code,
        capabilities=capabilities,
    )

    if task and task.error_message:
        response.error_message = task.error_message

    return response


@router.post("/materials/{material_id}/confirm-syllabus")
@limiter.limit("20/minute")
async def confirm_syllabus(request: Request, material_id: int):
    async with UnitOfWork() as uow:
        material = await uow.materials.get_by_id(material_id)
        if not material:
            raise HTTPException(status_code=404, detail="教材不存在")

        if material.status != "pending_review":
            raise HTTPException(status_code=400, detail="教材当前状态不支持确认操作")

        syllabus = await uow.syllabuses.get_by_material_id(material_id)

        await uow.materials.update(material, {
            "status": "ready",
            "review_status": "approved",
        })

        if syllabus:
            await uow.syllabuses.update(syllabus, {"review_status": "approved"})

    return {"status": "ok", "message": "大纲已确认，结构化教学模式已开启"}


@router.post("/materials/{material_id}/reject-syllabus")
@limiter.limit("20/minute")
async def reject_syllabus(request: Request, material_id: int):
    async with UnitOfWork() as uow:
        material = await uow.materials.get_by_id(material_id)
        if not material:
            raise HTTPException(status_code=404, detail="教材不存在")

        if material.status != "pending_review":
            raise HTTPException(status_code=400, detail="教材当前状态不支持拒绝操作")

        await uow.materials.update(material, {
            "status": "indexed",
            "review_status": "rejected",
        })

    return {"status": "ok", "message": "大纲已拒绝，将使用自由对话模式"}


@router.post("/materials/{material_id}/edit-syllabus")
@limiter.limit("20/minute")
async def edit_syllabus(request: Request, material_id: int, data: SyllabusEditRequest):
    async with UnitOfWork() as uow:
        material = await uow.materials.get_by_id(material_id)
        if not material:
            raise HTTPException(status_code=404, detail="教材不存在")

        syllabus = await uow.syllabuses.get_by_material_id(material_id)
        if not syllabus:
            raise HTTPException(status_code=404, detail="大纲不存在")

        update_data = {"review_status": "pending"}
        if data.name:
            update_data["name"] = data.name
        if data.total_days:
            update_data["total_days"] = data.total_days
        if data.content:
            update_data["content"] = data.content

        await uow.syllabuses.update(syllabus, update_data)

        await uow.materials.update(material, {
            "status": "pending_review",
            "review_status": "pending",
        })

    return {"status": "ok", "message": "大纲已更新，请重新确认"}


@router.get("/syllabus")
@limiter.limit("60/minute")
async def get_curriculum_syllabus(request: Request):
    from app.graph.knowledge_graph import KnowledgeGraph
    import yaml
    from pathlib import Path
    import os
    import sys

    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    syllabus_file = os.path.join(base_dir, "content", "syllabus.yaml")

    try:
        with open(syllabus_file, "r", encoding="utf-8") as f:
            syllabus = yaml.safe_load(f)
        return syllabus
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="课程大纲不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载课程大纲失败: {str(e)}")


@router.get("/modules")
@limiter.limit("60/minute")
async def get_curriculum_modules(request: Request):
    from app.graph.knowledge_graph import KnowledgeGraph
    from pathlib import Path
    import os
    import sys

    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    modules_dir = os.path.join(base_dir, "content", "modules")
    modules = []

    from app.main import _narrative_engine
    if _narrative_engine:
        kg = _narrative_engine.graph
        for pid, meta in kg.get_all_points().items():
            modules.append({
                "id": meta.id,
                "name": meta.name,
                "module_name": meta.module_name,
                "difficulty": meta.difficulty,
                "key_concepts": meta.key_concepts,
                "teaching_hints": meta.teaching_hints,
                "suggested_questions": meta.suggested_questions,
                "prerequisites": meta.prerequisites,
            })

    return modules


@router.post("/assessment/generate")
@limiter.limit("10/minute")
async def generate_assessment(request: Request, body: AssessmentGenerateRequest):
    """Generate a quiz for a given knowledge point using LLM"""
    from app.api.v1.ws import get_narrative_engine
    engine = get_narrative_engine()
    if not engine or not engine.assessment:
        raise HTTPException(status_code=503, detail="AssessmentEngine not initialized")

    result = await engine.generate_quiz(
        point_id=body.point_id,
        character_id=body.character_id,
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/progress/{point_id}")
@limiter.limit("30/minute")
async def get_point_progress(request: Request, point_id: str):
    """Get learning progress for a specific knowledge point"""
    async with UnitOfWork() as uow:
        from models.learning_progress import LearningProgress
        from sqlalchemy import select
        result = await uow.session.execute(
            select(LearningProgress).where(
                LearningProgress.knowledge_point_id == point_id
            )
        )
        progress = result.scalar_one_or_none()
        if progress:
            return {
                "point_id": progress.knowledge_point_id,
                "mastery_level": progress.mastery_level,
                "status": progress.status,
                "attempts": progress.attempts,
                "last_reviewed_at": str(progress.last_reviewed_at) if progress.last_reviewed_at else None,
            }
        return {"point_id": point_id, "mastery_level": 0, "status": "locked", "attempts": 0}