import pytest
import yaml
from pathlib import Path

from app.graph.knowledge_graph import KnowledgeGraph, PointMeta


@pytest.fixture
def kg():
    return KnowledgeGraph()


@pytest.fixture
def modules_dir(tmp_path):
    """Create temp YAML modules for load_from_yaml tests."""
    mod_a = {
        "id": "mod_a",
        "name": "Module A",
        "order": 1,
        "prerequisites": [],
        "knowledge_points": [
            {
                "id": "point_a1",
                "name": "Point A1",
                "difficulty": 1,
                "prerequisites": [],
            },
            {
                "id": "point_a2",
                "name": "Point A2",
                "difficulty": 2,
                "prerequisites": ["point_a1"],
            },
        ],
    }
    mod_b = {
        "id": "mod_b",
        "name": "Module B",
        "order": 2,
        "prerequisites": ["point_a1"],
        "knowledge_points": [
            {
                "id": "point_b1",
                "name": "Point B1",
                "difficulty": 2,
                "prerequisites": ["point_a2"],
            },
        ],
    }
    for mod in [mod_a, mod_b]:
        filepath = tmp_path / f"{mod['id']}.yaml"
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(mod, f, allow_unicode=True)
    return str(tmp_path)


class TestKnowledgeGraphLoadFromYaml:
    def test_load_registers_all_points(self, kg, modules_dir):
        kg.load_from_yaml(modules_dir)
        assert "point_a1" in kg._point_meta
        assert "point_a2" in kg._point_meta
        assert "point_b1" in kg._point_meta

    def test_load_sets_point_metadata(self, kg, modules_dir):
        kg.load_from_yaml(modules_dir)
        p = kg._point_meta["point_a1"]
        assert p.name == "Point A1"
        assert p.module_id == "mod_a"
        assert p.difficulty == 1

    def test_load_resolves_explicit_prereqs(self, kg, modules_dir):
        kg.load_from_yaml(modules_dir)
        assert "point_a1" in kg._graph["point_a2"]
        assert "point_a2" in kg._graph["point_b1"]

    def test_load_resolves_module_prereqs_after_all_points_loaded(self, kg, modules_dir):
        """Module-level prereqs should be applied even when the target
        point is in a different (alphabetically later) file."""
        kg.load_from_yaml(modules_dir)
        # point_b1 should have mod_b's prereqs (point_a1) as an ancestor
        # via module_prereqs, which means point_b1 depends on point_a1
        assert "point_a1" in kg._graph["point_b1"]

    def test_load_nonexistent_directory(self, kg):
        kg.load_from_yaml("/nonexistent/path")
        assert len(kg._point_meta) == 0

    def test_module_order_preserved(self, kg, modules_dir):
        kg.load_from_yaml(modules_dir)
        assert kg._module_order["mod_a"] == 1
        assert kg._module_order["mod_b"] == 2


class TestKnowledgeGraphLoadFromSyllabus:
    def test_load_from_dict(self, kg):
        syllabus = {
            "modules": [
                {
                    "id": "mod_x",
                    "name": "Module X",
                    "order": 0,
                    "prerequisites": [],
                    "knowledge_points": [
                        {"id": "p1", "name": "P1", "difficulty": 1, "prerequisites": []},
                        {"id": "p2", "name": "P2", "difficulty": 2, "prerequisites": ["p1"]},
                    ],
                }
            ]
        }
        kg.load_from_syllabus_content(syllabus)
        assert "p1" in kg._point_meta
        assert "p2" in kg._point_meta
        assert "p1" in kg._graph["p2"]

    def test_cross_module_prereqs_resolve_correctly(self, kg):
        """Module-level prereqs referencing points from later modules
        should still be resolved (two-pass fix)."""
        syllabus = {
            "modules": [
                {
                    "id": "mod1",
                    "name": "Module 1",
                    "order": 1,
                    "prerequisites": ["p_b"],
                    "knowledge_points": [
                        {"id": "p_a", "name": "A", "difficulty": 1, "prerequisites": []},
                    ],
                },
                {
                    "id": "mod2",
                    "name": "Module 2",
                    "order": 2,
                    "prerequisites": [],
                    "knowledge_points": [
                        {"id": "p_b", "name": "B", "difficulty": 1, "prerequisites": []},
                    ],
                },
            ]
        }
        kg.load_from_syllabus_content(syllabus)
        # p_a should depend on p_b via mod1's module-level prerequisite
        assert "p_b" in kg._graph["p_a"]


class TestKnowledgeGraphGetNextUnlocked:
    def test_nothing_mastered_returns_roots(self, kg, modules_dir):
        kg.load_from_yaml(modules_dir)
        unlocked = kg.get_next_unlocked(set())
        assert "point_a1" in unlocked
        # point_a2 requires point_a1, not unlocked yet
        assert "point_a2" not in unlocked

    def test_mastering_root_unlocks_dependent(self, kg, modules_dir):
        kg.load_from_yaml(modules_dir)
        unlocked = kg.get_next_unlocked({"point_a1"})
        assert "point_a2" in unlocked

    def test_all_mastered_returns_empty(self, kg, modules_dir):
        kg.load_from_yaml(modules_dir)
        all_points = {"point_a1", "point_a2", "point_b1"}
        unlocked = kg.get_next_unlocked(all_points)
        assert unlocked == []


class TestKnowledgeGraphGetLearningPath:
    def test_topological_order(self, kg, modules_dir):
        kg.load_from_yaml(modules_dir)
        path = kg.get_learning_path(set())
        # point_a1 must come before point_a2
        assert path.index("point_a1") < path.index("point_a2")
        # point_a2 must come before point_b1
        assert path.index("point_a2") < path.index("point_b1")

    def test_path_contains_all_points(self, kg, modules_dir):
        kg.load_from_yaml(modules_dir)
        path = kg.get_learning_path(set())
        assert set(path) == {"point_a1", "point_a2", "point_b1"}