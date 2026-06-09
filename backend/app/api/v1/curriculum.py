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

        syllabus = await uow.syllabuses.get_by_material_id(material_id)

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
        syllabus_preview=syllabus.content if syllabus and syllabus.content else None,
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


@router.get("/materials/generatable")
@limiter.limit("30/minute")
async def list_generatable_materials(request: Request):
    """List materials that have content and can generate a syllabus"""
    async with UnitOfWork() as uow:
        all_materials = await uow.materials.get_all()
        results = []
        for m in all_materials:
            if m.content and len(m.content.strip()) > 100:
                syllabus = await uow.syllabuses.get_by_material_id(m.id)
                results.append({
                    "id": m.id,
                    "title": m.title,
                    "status": m.status,
                    "char_count": m.char_count or len(m.content),
                    "has_syllabus": syllabus is not None,
                    "syllabus_status": syllabus.review_status if syllabus else None,
                })
    return results


@router.api_route("/materials/{material_id}/generate-outline", methods=["GET", "POST"])
@limiter.limit("5/minute")
async def generate_outline(request: Request, material_id: int):
    """Trigger LLM outline generation for a material"""
    from app.tasks.material_pipeline import _generate_outline

    async with UnitOfWork() as uow:
        material = await uow.materials.get_by_id(material_id)
        if not material:
            raise HTTPException(status_code=404, detail="教材不存在")
        if not material.content or len(material.content.strip()) < 100:
            raise HTTPException(status_code=400, detail="教材内容不足，无法生成大纲")
        text_content = material.content

    try:
        outline = await _generate_outline(text_content, UnitOfWork)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Outline generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"大纲生成失败: {str(e)}")

    async with UnitOfWork() as uow:
        material = await uow.materials.get_by_id(material_id)
        existing = await uow.syllabuses.get_by_material_id(material_id)
        if existing:
            await uow.syllabuses.update(existing, {
                "name": outline.get("name", "自动生成大纲"),
                "total_days": outline.get("total_days", 60),
                "content": outline,
                "generated_by": "llm",
                "review_status": "pending",
            })
        else:
            await uow.syllabuses.create({
                "material_id": material_id,
                "name": outline.get("name", "自动生成大纲"),
                "total_days": outline.get("total_days", 60),
                "content": outline,
                "generated_by": "llm",
                "review_status": "pending",
            })
        if material:
            await uow.materials.update(material, {
                "status": "pending_review",
                "review_status": "pending",
            })

    return {"status": "ok", "syllabus": outline}


@router.get("/syllabuses")
@limiter.limit("60/minute")
async def list_syllabuses(request: Request):
    """List all syllabuses grouped by material"""
    async with UnitOfWork() as uow:
        all_syllabuses = await uow.syllabuses.get_all_with_material()
        results = []
        for s in all_syllabuses:
            material_title = ""
            if s.material_id:
                material = await uow.materials.get_by_id(s.material_id)
                if material:
                    material_title = material.title or f"教材#{material.id}"
            results.append({
                "id": s.id,
                "material_id": s.material_id,
                "material_title": material_title,
                "name": s.name,
                "total_days": s.total_days,
                "generated_by": s.generated_by,
                "review_status": s.review_status,
                "created_at": str(s.created_at) if s.created_at else None,
            })
    return results


@router.get("/syllabus")
@limiter.limit("60/minute")
async def get_curriculum_syllabus(request: Request, material_id: Optional[int] = None):
    async with UnitOfWork() as uow:
        if material_id:
            syllabus = await uow.syllabuses.get_by_material_id(material_id)
            if syllabus:
                return syllabus.content
        else:
            approved = await uow.syllabuses.get_approved()
            if approved:
                latest = approved[-1]
                return latest.content

    import yaml
    import os
    import sys

    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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
async def get_curriculum_modules(request: Request, material_id: Optional[int] = None):
    from app.api.v1.ws import get_narrative_engine

    modules = []

    async with UnitOfWork() as uow:
        if material_id:
            syllabus = await uow.syllabuses.get_by_material_id(material_id)
            if syllabus and syllabus.content and "modules" in syllabus.content:
                for mod in syllabus.content.get("modules", []):
                    if not mod.get("id") and not mod.get("name"):
                        continue
                    module_data = {
                        "id": mod.get("id", ""),
                        "name": mod.get("name", ""),
                        "order": mod.get("order", 0),
                        "estimated_hours": mod.get("estimated_hours", 0),
                        "prerequisites": mod.get("prerequisites", []),
                        "knowledge_points": [
                            {
                                "id": kp.get("id", ""),
                                "name": kp.get("name", ""),
                                "difficulty": kp.get("difficulty", 1),
                                "key_concepts": kp.get("key_concepts", []),
                                "prerequisites": kp.get("prerequisites", []),
                            }
                            for kp in mod.get("knowledge_points", [])
                        ],
                    }
                    modules.append(module_data)
                if modules:
                    return modules
        else:
            approved = await uow.syllabuses.get_approved()
            if approved:
                latest = approved[-1]
                if latest.content and "modules" in latest.content:
                    for mod in latest.content.get("modules", []):
                        if not mod.get("id") and not mod.get("name"):
                            continue
                        module_data = {
                            "id": mod.get("id", ""),
                            "name": mod.get("name", ""),
                            "order": mod.get("order", 0),
                            "estimated_hours": mod.get("estimated_hours", 0),
                            "prerequisites": mod.get("prerequisites", []),
                            "knowledge_points": [
                                {
                                    "id": kp.get("id", ""),
                                    "name": kp.get("name", ""),
                                    "difficulty": kp.get("difficulty", 1),
                                    "key_concepts": kp.get("key_concepts", []),
                                    "prerequisites": kp.get("prerequisites", []),
                                }
                                for kp in mod.get("knowledge_points", [])
                            ],
                        }
                        modules.append(module_data)
                    if modules:
                        return modules

    engine = get_narrative_engine()
    if engine:
        kg = engine.graph
        module_groups = {}
        for pid, meta in kg.get_all_points().items():
            mid = meta.module_name
            if mid not in module_groups:
                module_groups[mid] = {
                    "id": mid,
                    "name": mid,
                    "knowledge_points": [],
                    "prerequisites": [],
                }
            module_groups[mid]["knowledge_points"].append({
                "id": meta.id,
                "name": meta.name,
                "module_name": meta.module_name,
                "difficulty": meta.difficulty,
                "key_concepts": meta.key_concepts,
                "teaching_hints": meta.teaching_hints,
                "suggested_questions": meta.suggested_questions,
                "prerequisites": meta.prerequisites,
            })
        modules = list(module_groups.values())

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


@router.get("/progress-summary")
@limiter.limit("30/minute")
async def get_progress_summary(request: Request):
    """Get overall learning progress summary for the dashboard"""
    point_name_map: dict[str, str] = {}
    async with UnitOfWork() as uow:
        all_progress = await uow.learning_progress.get_all()
        approved_syllabi = await uow.syllabuses.get_approved()
        for syllabus in approved_syllabi:
            content = syllabus.content or {}
            for mod in content.get("modules", []):
                for kp in mod.get("knowledge_points", []):
                    pid = kp.get("id")
                    pname = kp.get("name")
                    if pid and pname and pid not in point_name_map:
                        point_name_map[pid] = pname

    total = len(all_progress)
    mastered = sum(1 for p in all_progress if p.status == "mastered")
    learning = sum(1 for p in all_progress if p.status == "learning")
    locked = sum(1 for p in all_progress if p.status == "locked")
    avg_mastery = sum(p.mastery_level for p in all_progress) / max(total, 1)

    point_details = []
    for p in all_progress:
        point_details.append({
            "point_id": p.knowledge_point_id,
            "point_name": point_name_map.get(p.knowledge_point_id),
            "status": p.status,
            "mastery_level": round(p.mastery_level, 2),
            "attempts": p.attempts,
            "weak_areas": p.weak_areas or [],
        })

    return {
        "progress_summary": {
            "total_points": total,
            "mastered": mastered,
            "learning": learning,
            "locked": locked,
            "avg_mastery": round(avg_mastery, 2),
            "completion_rate": round(mastered / max(total, 1) * 100, 1),
        },
        "point_details": point_details,
    }


class ActivateSyllabusRequest(BaseModel):
    material_id: int


@router.post("/activate")
@limiter.limit("10/minute")
async def activate_syllabus(request: Request, body: ActivateSyllabusRequest):
    from app.api.v1.ws import get_narrative_engine

    engine = get_narrative_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="叙事引擎未初始化")

    result = await engine.activate_syllabus(body.material_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result