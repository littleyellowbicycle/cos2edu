"""大纲质量校验：在 outlining 之后、pending_review 之前对 LLM 生成的大纲做基本把关。

校验规则（内存环境，不依赖外部服务）：
1. 大纲非空：必须是字典，包含非空名称，且 modules 为非空列表；
2. 知识点可被解析：每个知识点必须有非空字符串 id / name，id 全局唯一；
3. 前置依赖在知识图谱中闭合：每个 prerequisites 条目必须引用已声明的知识点，
   不能自依赖，且依赖图无环。
"""
from dataclasses import dataclass, field
from typing import Optional

from app.core.logging_config import get_logger
from app.schemas.enums import QualityCheckErrorCode

logger = get_logger(__name__)

# 质量门阈值：一份可进入人工审核的大纲至少要包含这么多个合法知识点。
# 边界值：恰好等于阈值 → 通过；少于阈值 → 拒绝。
MIN_KNOWLEDGE_POINTS = 1


@dataclass
class QualityCheckResult:
    passed: bool
    reasons: list[str] = field(default_factory=list)
    error_code: Optional[str] = None
    knowledge_points: list[dict] = field(default_factory=list)

    def add_reason(self, code: str, message: str) -> None:
        self.reasons.append(f"[{code}] {message}")
        if self.error_code is None:
            self.error_code = code


def _iter_knowledge_points(outline: dict) -> list[tuple[dict, dict]]:
    """Return (module, knowledge_point) pairs across all modules."""
    pairs: list[tuple[dict, dict]] = []
    for module in outline.get("modules", []) or []:
        if not isinstance(module, dict):
            continue
        for kp in module.get("knowledge_points", []) or []:
            if isinstance(kp, dict):
                pairs.append((module, kp))
    return pairs


def _detect_cycle(kp_id: str, graph: dict[str, list[str]], visiting: set, visited: set) -> bool:
    """DFS cycle detection; returns True when a cycle involving kp_id is found."""
    if kp_id in visiting:
        return True
    if kp_id in visited:
        return False
    visiting.add(kp_id)
    for dep in graph.get(kp_id, []):
        if _detect_cycle(dep, graph, visiting, visited):
            return True
    visiting.discard(kp_id)
    visited.add(kp_id)
    return False


def validate_outline(outline) -> QualityCheckResult:
    """Validate a raw LLM outline dict. Pure function, safe to call in tests."""
    result = QualityCheckResult(passed=True)

    if not isinstance(outline, dict):
        result.passed = False
        result.add_reason(QualityCheckErrorCode.EMPTY_OUTLINE, "大纲不是有效的 JSON 对象")
        return result

    name = outline.get("name")
    if not name or not str(name).strip():
        result.passed = False
        result.add_reason(QualityCheckErrorCode.EMPTY_OUTLINE, "大纲缺少非空名称(name)")

    modules = outline.get("modules")
    if not isinstance(modules, list) or not modules:
        result.passed = False
        result.add_reason(QualityCheckErrorCode.NO_MODULES, "大纲必须包含非空的 modules 列表")
        return result

    declared_ids: set[str] = set()
    prereq_graph: dict[str, list[str]] = {}

    for mod_idx, module in enumerate(modules):
        if not isinstance(module, dict):
            result.passed = False
            result.add_reason(
                QualityCheckErrorCode.INVALID_MODULE,
                f"第 {mod_idx + 1} 个模块不是对象: {type(module).__name__}",
            )
            continue

        if not module.get("id") and not module.get("name"):
            result.passed = False
            result.add_reason(
                QualityCheckErrorCode.INVALID_MODULE,
                f"第 {mod_idx + 1} 个模块缺少 id 与 name",
            )

        for kp_idx, kp in enumerate(module.get("knowledge_points", []) or []):
            if not isinstance(kp, dict):
                result.passed = False
                result.add_reason(
                    QualityCheckErrorCode.MISSING_KP_ID,
                    f"模块[{module.get('id') or module.get('name') or mod_idx}]第 {kp_idx + 1} 个知识点不是对象",
                )
                continue

            kp_id = kp.get("id")
            if not kp_id or not str(kp_id).strip():
                result.passed = False
                result.add_reason(
                    QualityCheckErrorCode.MISSING_KP_ID,
                    f"模块[{module.get('id') or module.get('name') or mod_idx}]第 {kp_idx + 1} 个知识点缺少 id",
                )
                continue
            kp_id = str(kp_id).strip()

            if not kp.get("name") or not str(kp.get("name")).strip():
                result.passed = False
                result.add_reason(
                    QualityCheckErrorCode.MISSING_KP_NAME,
                    f"知识点[{kp_id}]缺少 name",
                )

            if kp_id in declared_ids:
                result.passed = False
                result.add_reason(
                    QualityCheckErrorCode.DUPLICATE_KP_ID,
                    f"知识点 id 重复: {kp_id}",
                )
            declared_ids.add(kp_id)

            prereqs = kp.get("prerequisites", []) or []
            if not isinstance(prereqs, list):
                result.passed = False
                result.add_reason(
                    QualityCheckErrorCode.INVALID_PREREQUISITE_TYPE,
                    f"知识点[{kp_id}]的 prerequisites 必须是列表",
                )
                prereqs = []
            else:
                prereqs = [str(p).strip() for p in prereqs]

            resolved: list[str] = []
            for prereq in prereqs:
                if not prereq:
                    continue
                if prereq == kp_id:
                    result.passed = False
                    result.add_reason(
                        QualityCheckErrorCode.SELF_PREREQUISITE,
                        f"知识点[{kp_id}]不能以自身为前置依赖",
                    )
                    continue
                resolved.append(prereq)
            # Accumulate: duplicate ids may each carry their own prerequisites,
            # and overwriting would silently drop the earlier edge.
            prereq_graph.setdefault(kp_id, []).extend(resolved)
            result.knowledge_points.append(kp)

    # Threshold gate: at least MIN_KNOWLEDGE_POINTS valid knowledge points.
    valid_point_count = len(declared_ids)
    if valid_point_count < MIN_KNOWLEDGE_POINTS:
        result.passed = False
        result.add_reason(
            QualityCheckErrorCode.NO_KNOWLEDGE_POINTS,
            f"大纲仅包含 {valid_point_count} 个知识点，少于最低要求 {MIN_KNOWLEDGE_POINTS} 个",
        )

    # Closure check: every prerequisite must reference a declared knowledge point
    for kp_id, resolved in prereq_graph.items():
        for prereq in resolved:
            if prereq not in declared_ids:
                result.passed = False
                result.add_reason(
                    QualityCheckErrorCode.UNDECLARED_PREREQUISITE,
                    f"知识点[{kp_id}]的前置依赖[{prereq}]未在大纲中声明",
                )

    # Cycle detection over the declared (and resolved) graph
    if result.passed:
        visited: set[str] = set()
        for kp_id in prereq_graph:
            if _detect_cycle(kp_id, prereq_graph, set(), visited):
                result.passed = False
                result.add_reason(
                    QualityCheckErrorCode.CYCLIC_PREREQUISITE,
                    "知识点前置依赖存在循环，无法形成学习路径",
                )
                break

    if not result.passed:
        logger.warning(f"Outline quality check failed: {len(result.reasons)} reason(s)")
    return result


# Backwards/alias: the stage is referred to as check_outline_quality in the
# product docs; validate_outline is the canonical implementation.
check_outline_quality = validate_outline

__all__ = ["validate_outline", "check_outline_quality", "QualityCheckResult", "MIN_KNOWLEDGE_POINTS"]
