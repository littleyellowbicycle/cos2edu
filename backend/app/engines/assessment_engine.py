from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

from app.graph.knowledge_graph import KnowledgeGraph
from app.engines.character_engine import CharacterEngine
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


@dataclass
class AssessmentResult:
    point_id: str
    score: float
    passed: bool
    mastery_level: float
    status: str
    feedback: str
    attempts: int


class AssessmentEngine:
    """考核引擎：生成测验、评分、判定掌握度"""

    MASTERY_THRESHOLD = 0.7
    PASS_THRESHOLD = 0.6
    MAX_ATTEMPTS = 3
    PASSING_THRESHOLD = 0.6

    def __init__(
        self,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        character_engine: Optional[CharacterEngine] = None,
    ):
        self.graph = knowledge_graph
        self.character_engine = character_engine

    # --- LLM-based quiz generation (remote) ---

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

        char_style = ""
        if self.character_engine:
            character = self.character_engine.get_character(character_id)
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

        point_name = point_id
        if self.graph:
            point_meta = self.graph.get_point(point_id)
            if point_meta:
                point_name = point_meta.name

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

    # --- Template-based quiz generation (local) ---

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
            question_text = f"关于「{concept}」，以下哪个说法是正确的？"
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
                feedback = "优秀！你已经完全掌握了这个知识点。"
            elif mastery_level >= 0.7:
                feedback = "不错！你对这个知识点的理解较好，可以继续深入。"
            else:
                feedback = "及格了，但还需要加强练习来巩固理解。"
        else:
            feedback = "还需要再努力一下。建议回顾相关概念后再次尝试。"

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
            "上述说法是正确的",
            "上述说法是错误的",
            "部分正确，但需要更多条件",
            "无法确定",
        ]

    def _generate_concept_options(self, concept: str, all_concepts: list[str]) -> list[str]:
        other = [c for c in all_concepts if c != concept]
        return [
            f"{concept}是核心概念",
            f"{other[0] if other else '其他概念'}更重要" if other else "这个概念不重要",
            f"{concept}只在特定条件下适用",
            "以上都不对",
        ]
