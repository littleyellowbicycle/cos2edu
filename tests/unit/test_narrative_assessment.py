import pytest
import os
from unittest.mock import MagicMock, patch

from app.engines.assessment_engine import AssessmentEngine, Quiz, QuizResult
from app.engines.narrative_engine import NarrativeEngine
from app.graph.knowledge_graph import KnowledgeGraph
from app.engines.world_state_engine import WorldStateEngine
from app.engines.character_engine import CharacterEngine
from app.engines.teaching_engine import TeachingEngine
from app.llm.context_budget import ContextBudget
from app.state.state_manager import StateManager

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "content")


class TestNarrativeAssessment:

    def setup_method(self):
        self.graph = KnowledgeGraph()
        self.assessment_engine = AssessmentEngine()
        self.world = WorldStateEngine(content_dir=CONTENT_DIR)
        self.characters = CharacterEngine(content_dir=CONTENT_DIR)
        self.budget = ContextBudget(total_tokens=4096)
        self.teaching = TeachingEngine(
            knowledge_graph=self.graph,
            character_engine=self.characters,
            context_budget=self.budget,
        )
        self.state_manager = MagicMock(spec=StateManager)
        self.engine = NarrativeEngine(
            knowledge_graph=self.graph,
            world_state_engine=self.world,
            character_engine=self.characters,
            teaching_engine=self.teaching,
            state_manager=self.state_manager,
            assessment_engine=self.assessment_engine,
        )

    def test_start_assessment_raises_for_unknown_point(self):
        with pytest.raises(ValueError, match="not found"):
            self.engine.start_assessment("nonexistent_point")

    def test_submit_assessment_raises_without_active_quiz(self):
        with pytest.raises(ValueError, match="No active quiz"):
            self.engine.submit_assessment_answer("perceptron", [0])

    def test_assessment_engine_is_default_injected(self):
        engine = NarrativeEngine(
            knowledge_graph=self.graph,
            world_state_engine=self.world,
            character_engine=self.characters,
            teaching_engine=self.teaching,
            state_manager=self.state_manager,
        )
        assert isinstance(engine.assessment, AssessmentEngine)

    def test_start_assessment_with_known_point(self):
        self.graph._point_meta["perceptron"] = MagicMock(
            id="perceptron",
            name="\u611f\u77e5\u673a",
            module_id="ml_basics",
            module_name="\u673a\u5668\u5b66\u4e60\u57fa\u7840",
            difficulty=2,
            estimated_minutes=30,
            key_concepts=["\u7ebf\u6027\u5206\u7c7b", "\u6fc0\u6d3b\u51fd\u6570"],
            suggested_questions=["\u611f\u77e5\u673a\u7684\u5c40\u9650\u6027\u662f\u4ec0\u4e48\uff1f"],
            exercises=[],
            prerequisites=[],
        )
        self.graph._graph["perceptron"] = set()
        quiz = self.engine.start_assessment("perceptron", num_questions=3)
        assert quiz.knowledge_point_id == "perceptron"
        assert len(quiz.questions) >= 1
        assert "perceptron" in self.engine._active_quizzes

    def test_submit_assessment_scoring(self):
        self.graph._point_meta["test_point"] = MagicMock(
            id="test_point",
            name="Test",
            module_id="mod1",
            module_name="Module 1",
            difficulty=1,
            estimated_minutes=10,
            key_concepts=["concept1"],
            suggested_questions=["What is concept1?"],
            exercises=[],
            prerequisites=[],
        )
        self.graph._graph["test_point"] = set()
        quiz = self.engine.start_assessment("test_point", num_questions=1)
        assert len(quiz.questions) >= 1
        result = self.engine.submit_assessment_answer("test_point", [0])
        assert isinstance(result, QuizResult)
        assert result.knowledge_point_id == "test_point"
        assert result.total_questions >= 1
        assert result.correct_count >= 0
        assert "test_point" not in self.engine._active_quizzes