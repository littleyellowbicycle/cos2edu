from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from app.graph.knowledge_graph import KnowledgeGraph
from app.engines.character_engine import CharacterEngine
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AssessmentResult:
    point_id: str
    score: float
    passed: bool
    mastery_level: float
    status: str
    feedback: str
    attempts: int


@dataclass
class QuizQuestion:
    question_id: str
    point_id: str
    question_type: str
    question_text: str
    options: list[str]
    correct_answer: str
    explanation: str
    difficulty: int


class AssessmentEngine:
    """考核引擎：生成测验、评分、判定掌握度"""

    MASTERY_THRESHOLD = 0.7
    PASS_THRESHOLD = 0.6
    MAX_ATTEMPTS = 3

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        character_engine: CharacterEngine,
    ):
        self.graph = knowledge_graph
        self.character_engine = character_engine

    def generate_quiz_prompt(
        self,
        point_data: dict,
        character_id: str,
        num_questions: int = 3,
    ) -> str:
        point_id = point_data.get("point_id", "")
        point_name = point_data.get("name", "")
        key_concepts = point_data.get("key_concepts", [])
        difficulty = point_data.get("difficulty", 1)
        exercises = point_data.get("exercises", [])

        character = self.character_engine.get_character(character_id)
        char_style = ""
        if character:
            char_style = f"以{character.name}的风格（{character.personality}）出题。"

        exercise_hint = ""
        if exercises:
            exercise_hint = f"\n参考练习题方向：{', '.join(exercises[:3])}"

        prompt = (
            f"你是一位考核出题专家。{char_style}\n\n"
            f"知识点：{point_name}\n"
            f"核心概念：{', '.join(key_concepts)}\n"
            f"难度：{difficulty}/5\n"
            f"题目数量：{num_questions}道\n{exercise_hint}\n\n"
            f"请严格按以下JSON格式输出（不要输出其他内容）：\n"
            f"{{\n"
            f'  "questions": [\n'
            f"    {{\n"
            f'      "question_type": "choice",\n'
            f'      "question_text": "题目内容",\n'
            f'      "options": ["选项A", "选项B", "选项C", "选项D"],\n'
            f'      "correct_answer": "选项A",\n'
            f'      "explanation": "答案解析"\n'
            f"    }},\n"
            f"    {{\n"
            f'      "question_type": "open",\n'
            f'      "question_text": "简答题",\n'
            f'      "correct_answer": "参考答案关键词",\n'
            f'      "explanation": "答案解析"\n'
            f"    }}\n"
            f"  ]\n"
            f"}}"
        )

        return prompt

    def evaluate_answer(
        self,
        question: dict,
        user_answer: str,
    ) -> dict:
        correct_answer = question.get("correct_answer", "")
        question_type = question.get("question_type", "choice")

        if question_type == "choice":
            is_correct = user_answer.strip() == correct_answer.strip()
            score = 1.0 if is_correct else 0.0
        else:
            is_correct = False
            score = 0.0
            correct_keywords = [kw.strip() for kw in correct_answer.split(",") if kw.strip()]
            if correct_keywords:
                matched = sum(1 for kw in correct_keywords if kw in user_answer)
                score = matched / len(correct_keywords)
                is_correct = score >= self.MASTERY_THRESHOLD

        return {
            "is_correct": is_correct,
            "score": score,
            "correct_answer": correct_answer,
            "explanation": question.get("explanation", ""),
        }

    def calculate_mastery(
        self,
        scores: list[float],
        attempts: int,
    ) -> float:
        if not scores:
            return 0.0
        avg_score = sum(scores) / len(scores)
        attempt_penalty = max(0, (attempts - 1)) * 0.1
        mastery = max(0.0, min(1.0, avg_score - attempt_penalty))
        return round(mastery, 2)

    def determine_status(self, mastery_level: float, attempts: int) -> str:
        if mastery_level >= self.MASTERY_THRESHOLD:
            return "mastered"
        elif mastery_level >= self.PASS_THRESHOLD:
            return "learning"
        elif attempts >= self.MAX_ATTEMPTS:
            return "review_needed"
        else:
            return "learning"

    def assess_point(
        self,
        point_id: str,
        scores: list[float],
        attempts: int,
    ) -> AssessmentResult:
        mastery_level = self.calculate_mastery(scores, attempts)
        passed = mastery_level >= self.MASTERY_THRESHOLD
        status = self.determine_status(mastery_level, attempts)

        point_meta = self.graph.get_point(point_id)
        point_name = point_meta.name if point_meta else point_id

        if passed:
            feedback = f"恭喜！你已经掌握了「{point_name}」，可以进入下一个知识点。"
        elif mastery_level >= self.PASS_THRESHOLD:
            feedback = f"你对「{point_name}」有基本理解，但还需要加强。建议再练习一下。"
        elif attempts >= self.MAX_ATTEMPTS:
            feedback = f"「{point_name}」需要重新复习。角色导师将会重新讲解这个知识点。"
        else:
            feedback = f"继续努力！你对「{point_name}」的理解还在发展中。"

        return AssessmentResult(
            point_id=point_id,
            score=sum(scores) / len(scores) if scores else 0.0,
            passed=passed,
            mastery_level=mastery_level,
            status=status,
            feedback=feedback,
            attempts=attempts,
        )

    def should_trigger_assessment(
        self,
        point_id: str,
        mastered_points: set[str],
        message_count: int,
        last_assessment_at: Optional[datetime] = None,
    ) -> bool:
        if point_id in mastered_points:
            return False
        if message_count < 3:
            return False
        if message_count % 5 != 0:
            return False
        if last_assessment_at:
            delta = (datetime.now() - last_assessment_at).total_seconds()
            if delta < 120:
                return False
        return True