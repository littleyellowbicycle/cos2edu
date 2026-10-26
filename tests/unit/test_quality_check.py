"""quality_check 阶段纯函数校验器单元测试（不触碰数据库/LLM）。"""
import pytest

from app.tasks.quality_check import validate_outline
from app.schemas.enums import QualityCheckErrorCode as Q


def _kp(kp_id: str, name: str = "知识点", prerequisites=None, **overrides) -> dict:
    point = {
        "id": kp_id,
        "name": name,
        "difficulty": 1,
        "key_concepts": [],
        "prerequisites": prerequisites or [],
    }
    point.update(overrides)
    return point


def _module(mod_id: str, points: list[dict]) -> dict:
    return {"id": mod_id, "name": f"模块{mod_id}", "order": 1, "knowledge_points": points}


class TestValidOutline:

    def test_valid_outline_passes(self):
        outline = {
            "name": "课程大纲",
            "total_days": 30,
            "modules": [
                _module("m1", [_kp("a", "A"), _kp("b", "B", ["a"])]),
                _module("m2", [_kp("c", "C", ["b"])]),
            ],
        }
        result = validate_outline(outline)
        assert result.passed is True
        assert result.error_code is None
        assert {p["id"] for p in result.knowledge_points} == {"a", "b", "c"}

    def test_outline_with_phases_passes(self):
        outline = {
            "name": "X",
            "phases": [{"name": "p1", "days": [1, 10], "modules": ["m1"]}],
            "modules": [_module("m1", [_kp("a")])],
        }
        assert validate_outline(outline).passed is True


class TestEmptyOutline:

    def test_none_rejected(self):
        result = validate_outline(None)
        assert result.passed is False
        assert result.error_code == Q.EMPTY_OUTLINE

    def test_non_dict_rejected(self):
        result = validate_outline(["not", "a", "dict"])
        assert result.passed is False
        assert result.error_code == Q.EMPTY_OUTLINE

    def test_missing_name_rejected(self):
        result = validate_outline({"modules": [_module("m1", [_kp("a")])]})
        assert result.passed is False
        assert Q.EMPTY_OUTLINE in result.reasons[0]

    def test_empty_modules_rejected(self):
        result = validate_outline({"name": "X", "modules": []})
        assert result.passed is False
        assert result.error_code == Q.NO_MODULES

    def test_missing_modules_key_rejected(self):
        result = validate_outline({"name": "X"})
        assert result.passed is False
        assert result.error_code == Q.NO_MODULES


class TestKnowledgePointParseable:

    def test_missing_kp_id_rejected(self):
        outline = {"name": "X", "modules": [_module("m1", [{"name": "无名", "prerequisites": []}])]}
        result = validate_outline(outline)
        assert result.passed is False
        assert result.error_code == Q.MISSING_KP_ID

    def test_missing_kp_name_rejected(self):
        outline = {"name": "X", "modules": [_module("m1", [{"id": "a", "prerequisites": []}])]}
        result = validate_outline(outline)
        assert result.passed is False
        assert result.error_code == Q.MISSING_KP_NAME

    def test_duplicate_kp_id_rejected(self):
        outline = {
            "name": "X",
            "modules": [
                _module("m1", [_kp("dup", "第一个"), _kp("dup", "第二个")]),
            ],
        }
        result = validate_outline(outline)
        assert result.passed is False
        assert result.error_code == Q.DUPLICATE_KP_ID
        assert any("dup" in r for r in result.reasons)

    def test_module_not_an_object_rejected(self):
        outline = {"name": "X", "modules": ["just a string"]}
        result = validate_outline(outline)
        assert result.passed is False
        assert result.error_code == Q.INVALID_MODULE

    def test_kp_not_an_object_rejected(self):
        outline = {"name": "X", "modules": [{"id": "m1", "knowledge_points": ["raw string"]}]}
        result = validate_outline(outline)
        assert result.passed is False
        assert result.error_code == Q.MISSING_KP_ID


class TestPrerequisiteClosure:

    def test_undeclared_prerequisite_rejected(self):
        outline = {
            "name": "X",
            "modules": [_module("m1", [_kp("a", "A", ["ghost"])]), _module("m2", [_kp("b", "B")])],
        }
        result = validate_outline(outline)
        assert result.passed is False
        assert result.error_code == Q.UNDECLARED_PREREQUISITE
        assert any("ghost" in r and "a" in r for r in result.reasons)

    def test_self_prerequisite_rejected(self):
        outline = {"name": "X", "modules": [_module("m1", [_kp("a", "A", ["a"])])]}
        result = validate_outline(outline)
        assert result.passed is False
        assert result.error_code == Q.SELF_PREREQUISITE

    def test_cyclic_prerequisite_rejected(self):
        outline = {
            "name": "X",
            "modules": [
                _module("m1", [
                    _kp("a", "A", ["c"]),
                    _kp("b", "B", ["a"]),
                    _kp("c", "C", ["b"]),
                ]),
            ],
        }
        result = validate_outline(outline)
        assert result.passed is False
        assert result.error_code == Q.CYCLIC_PREREQUISITE

    def test_prerequisites_not_a_list_rejected(self):
        outline = {
            "name": "X",
            "modules": [_module("m1", [{"id": "a", "name": "A", "prerequisites": "a,b"}])],
        }
        result = validate_outline(outline)
        assert result.passed is False
        assert result.error_code == Q.INVALID_PREREQUISITE_TYPE

    def test_chain_of_declared_prerequisites_passes(self):
        outline = {
            "name": "X",
            "modules": [_module("m1", [_kp("a"), _kp("b", prerequisites=["a"]), _kp("c", prerequisites=["b"])])],
        }
        assert validate_outline(outline).passed is True

    def test_reports_multiple_reasons(self):
        outline = {
            "name": "X",
            "modules": [
                {"id": "m1", "knowledge_points": [
                    {"id": "a", "name": "A", "prerequisites": ["ghost1"]},
                    {"id": "a", "name": "重复", "prerequisites": ["ghost2"]},
                ]},
            ],
        }
        result = validate_outline(outline)
        assert result.passed is False
        assert len(result.reasons) >= 3
        assert any("DUPLICATE_KP_ID" in r for r in result.reasons)
        assert sum("UNDECLARED_PREREQUISITE" in r for r in result.reasons) >= 2


# --------------------------------------------------------------------------- #
# 失败/边界路径：modules 为空 / 含非法类型、质量门阈值边界、别名
# --------------------------------------------------------------------------- #

class TestModulesShapeBoundary:

    def test_modules_is_none(self):
        result = validate_outline({"name": "X", "modules": None})
        assert result.passed is False
        assert result.error_code == Q.NO_MODULES

    def test_modules_is_string_not_list(self):
        result = validate_outline({"name": "X", "modules": "not-a-list"})
        assert result.passed is False
        assert result.error_code == Q.NO_MODULES

    @pytest.mark.parametrize("bad_module", ["a-string", 42, None, ["nested"], 3.14])
    def test_module_entries_of_illegal_type_rejected(self, bad_module):
        result = validate_outline({"name": "X", "modules": [bad_module]})
        assert result.passed is False
        assert result.error_code == Q.INVALID_MODULE
        assert any("INVALID_MODULE" in r for r in result.reasons)

    def test_module_without_knowledge_points_field_rejected_by_threshold(self):
        outline = {"name": "X", "modules": [{"id": "m1", "name": "空模块"}]}
        result = validate_outline(outline)
        assert result.passed is False
        assert result.error_code == Q.NO_KNOWLEDGE_POINTS

    def test_module_with_empty_kp_list_rejected_by_threshold(self):
        outline = {"name": "X", "modules": [_module("m1", [])]}
        result = validate_outline(outline)
        assert result.passed is False
        assert Q.NO_KNOWLEDGE_POINTS in result.reasons[0]

    def test_mixed_valid_and_illegal_modules_collects_reasons(self):
        outline = {
            "name": "X",
            "modules": [
                "garbage",
                _module("m1", [_kp("a", "A")]),
                99,
            ],
        }
        result = validate_outline(outline)
        assert result.passed is False
        assert sum("INVALID_MODULE" in r for r in result.reasons) == 2
        # 合法模块的知识点仍被解析
        assert "a" in {p["id"] for p in result.knowledge_points}


class TestThresholdBoundary:

    def test_exactly_minimum_knowledge_point_passes(self):
        """边界：恰好 MIN_KNOWLEDGE_POINTS=1 个合法知识点 → 通过。"""
        from app.tasks.quality_check import MIN_KNOWLEDGE_POINTS
        outline = {
            "name": "X",
            "modules": [_module("m1", [_kp("only", "唯一知识点")])],
        }
        result = validate_outline(outline)
        assert result.passed is True
        assert MIN_KNOWLEDGE_POINTS == 1

    def test_zero_valid_points_fails(self):
        outline = {
            "name": "X",
            "modules": [_module("m1", [{"name": "无id点", "prerequisites": []}])],
        }
        result = validate_outline(outline)
        assert result.passed is False
        assert result.error_code in (Q.MISSING_KP_ID, Q.NO_KNOWLEDGE_POINTS)


class TestAlias:

    def test_check_outline_quality_alias_equals_validate_outline(self):
        from app.tasks.quality_check import check_outline_quality
        outline = {"name": "X", "modules": [_module("m1", [_kp("a", "A")])]}
        assert check_outline_quality(outline).passed is True
        assert check_outline_quality is validate_outline
