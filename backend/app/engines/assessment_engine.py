from dataclasses import dataclass, field
from typing import Optional

from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class QuizQuestion:
    question_text: str
    options: list[str]
    correct_answer: int
    difficulty: int = 1


@dataclass
class Quiz:
    knowledge_point_id: str
    knowledge_point_name: str
    difficulty: int
    questions: list[QuizQuestion] = field(default_factory=list)


@dataclass
class QuizResult:
    knowledge_point_id: str
    mastery_level: float
    correct_count: int
    total_questions: int
    passed: bool
    feedback: str = ""


class AssessmentEngine:
    PASSING_THRESHOLD = 0.6

    def generate_quiz(
        self,
        knowledge_point: dict,
        num_questions: int = 4,
    ) -> Quiz:
        point_id = knowledge_point.get("id", "unknown")
        point_name = knowledge_point.get("name", "Unknown")
        difficulty = knowledge_point.get("difficulty", 1)
        key_concepts = knowledge_point.get("key_concepts", [])
        suggested = knowledge_point.get("suggested_questions", [])

        questions = []

        if suggested:
            for sq in suggested[:num_questions]:
                options = self._generate_options(sq, key_concepts)
                questions.append(QuizQuestion(
                    question_text=sq,
                    options=options,
                    correct_answer=0,
                    difficulty=difficulty,
                ))

        while len(questions) < num_questions and key_concepts:
            concept = key_concepts[len(questions) % len(key_concepts)]
            question_text = f"\u5173\u4e8e\u300c{concept}\u300d\uff0c\u4ee5\u4e0b\u54ea\u4e2a\u8bf4\u6cd5\u662f\u6b63\u786e\u7684\uff1f"
            options = self._generate_concept_options(concept, key_concepts)
            questions.append(QuizQuestion(
                question_text=question_text,
                options=options,
                correct_answer=0,
                difficulty=difficulty,
            ))

        return Quiz(
            knowledge_point_id=point_id,
            knowledge_point_name=point_name,
            difficulty=difficulty,
            questions=questions[:num_questions],
        )

    def score_quiz(
        self,
        knowledge_point_id: str,
        total_questions: int,
        correct_answers: int,
        previous_attempts: int = 0,
    ) -> QuizResult:
        base_mastery = correct_answers / total_questions if total_questions > 0 else 0

        attempt_bonus = min(0.1, previous_attempts * 0.05) if base_mastery >= self.PASSING_THRESHOLD else 0
        mastery_level = min(1.0, base_mastery + attempt_bonus)

        passed = mastery_level >= self.PASSING_THRESHOLD and correct_answers >= total_questions * 0.5

        if passed:
            if mastery_level >= 0.9:
                feedback = "\u4f18\u79c0\uff01\u4f60\u5df2\u7ecf\u5b8c\u5168\u638c\u63e1\u4e86\u8fd9\u4e2a\u77e5\u8bc6\u70b9\u3002"
            elif mastery_level >= 0.7:
                feedback = "\u4e0d\u9519\uff01\u4f60\u5bf9\u8fd9\u4e2a\u77e5\u8bc6\u70b9\u7684\u7406\u89e3\u8f83\u597d\uff0c\u53ef\u4ee5\u7ee7\u7eed\u6df1\u5165\u3002"
            else:
                feedback = "\u53ca\u683c\u4e86\uff0c\u4f46\u8fd8\u9700\u8981\u52a0\u5f3a\u7ec3\u4e60\u6765\u5dea\u56fa\u7406\u89e3\u3002"
        else:
            feedback = "\u8fd8\u9700\u8981\u518d\u52aa\u529b\u4e00\u4e0b\u3002\u5efa\u8bae\u56de\u987e\u76f8\u5173\u6982\u5ff5\u540e\u518d\u6b21\u5c1d\u8bd5\u3002"

        return QuizResult(
            knowledge_point_id=knowledge_point_id,
            mastery_level=round(mastery_level, 2),
            correct_count=correct_answers,
            total_questions=total_questions,
            passed=passed,
            feedback=feedback,
        )

    def _generate_options(self, question: str, key_concepts: list[str]) -> list[str]:
        return [
            "\u4e0a\u8ff0\u8bf4\u6cd5\u662f\u6b63\u786e\u7684",
            "\u4e0a\u8ff0\u8bf4\u6cd5\u662f\u9519\u8bef\u7684",
            "\u90e8\u5206\u6b63\u786e\uff0c\u4f46\u9700\u8981\u66f4\u591a\u6761\u4ef6",
            "\u65e0\u6cd5\u786e\u5b9a",
        ]

    def _generate_concept_options(self, concept: str, all_concepts: list[str]) -> list[str]:
        other = [c for c in all_concepts if c != concept]
        return [
            f"{concept}\u662f\u6838\u5fc3\u6982\u5ff5",
            f"{other[0] if other else '\u5176\u4ed6\u6982\u5ff5'}\u66f4\u91cd\u8981" if other else "\u8fd9\u4e2a\u6982\u5ff5\u4e0d\u91cd\u8981",
            f"{concept}\u53ea\u5728\u7279\u5b9a\u6761\u4ef6\u4e0b\u9002\u7528",
            "\u4ee5\u4e0a\u90fd\u4e0d\u5bf9",
        ]