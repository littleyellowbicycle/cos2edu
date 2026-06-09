import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PointMeta:
    id: str
    name: str
    module_id: str
    module_name: str
    difficulty: int = 1
    estimated_minutes: int = 30
    key_concepts: list = field(default_factory=list)
    teaching_hints: dict = field(default_factory=dict)
    suggested_questions: list = field(default_factory=list)
    exercises: list = field(default_factory=list)
    prerequisites: list = field(default_factory=list)


class KnowledgeGraph:
    """内存知识点依赖图，启动时从 YAML 加载"""

    def __init__(self):
        self._graph: dict[str, set[str]] = {}
        self._point_meta: dict[str, PointMeta] = {}
        self._module_order: dict[str, int] = {}

    def _collect_points(self, modules_dir: str) -> list[dict]:
        """Two-pass helper: first pass collects all raw point data, second resolves prereqs."""
        modules_path = Path(modules_dir)
        if not modules_path.exists():
            logger.warning(f"Modules directory not found: {modules_dir}")
            return []

        raw_points = []
        for module_file in sorted(modules_path.glob("*.yaml")):
            try:
                module = yaml.safe_load(module_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"Failed to load module {module_file}: {e}")
                continue
            if not module:
                continue
            module_id = module.get("id", module_file.stem)
            self._module_order[module_id] = module.get("order", 0)
            module_prereqs = module.get("prerequisites", [])
            module_name = module.get("name", module_id)
            for point in module.get("knowledge_points", []):
                pid = point.get("id", "")
                if not pid:
                    continue
                raw_points.append({
                    "pid": pid,
                    "point": point,
                    "module_id": module_id,
                    "module_name": module_name,
                    "module_prereqs": module_prereqs,
                })
        return raw_points

    def _resolve_prereqs(self, raw_prereq_ids: list[str]) -> set[str]:
        return {pid for pid in raw_prereq_ids if pid in self._point_meta}

    def load_from_yaml(self, modules_dir: str) -> None:
        self._graph.clear()
        self._point_meta.clear()
        self._module_order.clear()

        raw_points = self._collect_points(modules_dir)

        for rp in raw_points:
            self._point_meta[rp["pid"]] = PointMeta(
                id=rp["pid"],
                name=rp["point"].get("name", rp["pid"]),
                module_id=rp["module_id"],
                module_name=rp["module_name"],
                difficulty=rp["point"].get("difficulty", 1),
                estimated_minutes=rp["point"].get("estimated_minutes", 30),
                key_concepts=rp["point"].get("key_concepts", []),
                teaching_hints=rp["point"].get("teaching_hints", {}),
                suggested_questions=rp["point"].get("suggested_questions", []),
                exercises=rp["point"].get("exercises", []),
                prerequisites=list(rp["point"].get("prerequisites", [])),
            )

        for rp in raw_points:
            explicit_prereqs = self._resolve_prereqs(rp["point"].get("prerequisites", []))
            module_prereqs = self._resolve_prereqs(rp["module_prereqs"])
            self._graph[rp["pid"]] = explicit_prereqs | module_prereqs

        logger.info(f"KnowledgeGraph loaded: {len(self._point_meta)} points, {len(self._module_order)} modules")

    def get_next_unlocked(self, mastered: set[str]) -> list[str]:
        """返回所有前置已满足的、未掌握的知识点"""
        unlocked = []
        for pid, deps in self._graph.items():
            if pid not in mastered and deps.issubset(mastered):
                unlocked.append(pid)
        unlocked.sort(key=lambda pid: (self._module_order.get(self._point_meta[pid].module_id, 999), self._point_meta[pid].difficulty))
        return unlocked

    def get_learning_path(self, mastered: set[str]) -> list[str]:
        """拓扑排序，返回推荐学习路径"""
        path = []
        remaining = set(self._graph.keys()) - mastered
        available = set(mastered)

        while remaining:
            ready = [pid for pid in remaining if self._graph.get(pid, set()).issubset(available)]
            if not ready:
                ready = list(remaining)
            ready.sort(key=lambda pid: (self._module_order.get(self._point_meta[pid].module_id, 999), self._point_meta[pid].difficulty))
            next_point = ready[0]
            path.append(next_point)
            available.add(next_point)
            remaining.discard(next_point)

        return path

    def get_point(self, point_id: str) -> Optional[PointMeta]:
        return self._point_meta.get(point_id)

    def get_all_points(self) -> dict[str, PointMeta]:
        return dict(self._point_meta)

    def get_points_by_module(self, module_id: str) -> list[PointMeta]:
        return [p for p in self._point_meta.values() if p.module_id == module_id]

    def reload(self, modules_dir: str) -> None:
        self.load_from_yaml(modules_dir)

    def load_from_syllabus_content(self, syllabus_content: dict) -> None:
        self._graph.clear()
        self._point_meta.clear()
        self._module_order.clear()

        raw_points = []
        modules = syllabus_content.get("modules", [])
        for mod_idx, mod in enumerate(modules):
            module_id = mod.get("id", f"module_{mod_idx}")
            module_name = mod.get("name", module_id)
            self._module_order[module_id] = mod.get("order", mod_idx)
            module_prereqs = mod.get("prerequisites", [])
            for point in mod.get("knowledge_points", []):
                pid = point.get("id", "")
                if not pid:
                    continue
                raw_points.append({
                    "pid": pid,
                    "point": point,
                    "module_id": module_id,
                    "module_name": module_name,
                    "module_prereqs": module_prereqs,
                })

        for rp in raw_points:
            self._point_meta[rp["pid"]] = PointMeta(
                id=rp["pid"],
                name=rp["point"].get("name", rp["pid"]),
                module_id=rp["module_id"],
                module_name=rp["module_name"],
                difficulty=rp["point"].get("difficulty", 1),
                estimated_minutes=rp["point"].get("estimated_minutes", 30),
                key_concepts=rp["point"].get("key_concepts", []),
                teaching_hints=rp["point"].get("teaching_hints", {}),
                suggested_questions=rp["point"].get("suggested_questions", []),
                exercises=rp["point"].get("exercises", []),
                prerequisites=list(rp["point"].get("prerequisites", [])),
            )

        for rp in raw_points:
            explicit_prereqs = self._resolve_prereqs(rp["point"].get("prerequisites", []))
            module_prereqs = self._resolve_prereqs(rp["module_prereqs"])
            self._graph[rp["pid"]] = explicit_prereqs | module_prereqs

        logger.info(f"KnowledgeGraph loaded from syllabus: {len(self._point_meta)} points, {len(self._module_order)} modules")