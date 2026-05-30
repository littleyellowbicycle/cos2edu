from app.engines.assessment_engine import AssessmentEngine, Quiz, QuizQuestion, QuizResult


class TestAssessmentEngineGenerateQuiz:

    def setup_method(self):
        self.engine = AssessmentEngine()

    def test_generate_quiz_from_knowledge_point(self):
        point = {
            "id": "perceptron",
            "name": "\u611f\u77e5\u673a",
            "difficulty": 2,
            "key_concepts": ["\u7ebf\u6027\u5206\u7c7b", "\u6fc0\u6d3b\u51fd\u6570", "\u635f\u5931\u51fd\u6570"],
            "suggested_questions": ["\u5982\u679c\u6570\u636e\u4e0d\u662f\u7ebf\u6027\u53ef\u5206\u7684\uff0c\u611f\u77e5\u673a\u4f1a\u53d1\u751f\u4ec0\u4e48\uff1f"],
        }
        quiz = self.engine.generate_quiz(point, num_questions=3)
        assert quiz.knowledge_point_id == "perceptron"
        assert quiz.knowledge_point_name == "\u611f\u77e5\u673a"
        assert quiz.difficulty == 2
        assert len(quiz.questions) <= 3
        assert len(quiz.questions) >= 1

    def test_generate_quiz_with_no_suggested_questions(self):
        point = {
            "id": "backprop",
            "name": "\u53cd\u5411\u4f20\u64ad",
            "difficulty": 3,
            "key_concepts": ["\u68af\u5ea6\u4e0b\u964d", "\u94fe\u5f0f\u6cd5\u5219", "\u8ba1\u7b97\u56fe"],
            "suggested_questions": [],
        }
        quiz = self.engine.generate_quiz(point, num_questions=4)
        assert quiz.knowledge_point_id == "backprop"
        assert len(quiz.questions) <= 4
        assert all(q.question_text for q in quiz.questions)

    def test_generate_quiz_with_empty_concepts(self):
        point = {
            "id": "test",
            "name": "Test",
            "difficulty": 1,
            "key_concepts": [],
            "suggested_questions": [],
        }
        quiz = self.engine.generate_quiz(point, num_questions=3)
        assert len(quiz.questions) == 0


class TestAssessmentEngineScoreQuiz:

    def setup_method(self):
        self.engine = AssessmentEngine()

    def test_score_quiz_pass(self):
        result = self.engine.score_quiz(
            knowledge_point_id="perceptron",
            total_questions=4,
            correct_answers=3,
        )
        assert result.mastery_level == 0.75
        assert result.knowledge_point_id == "perceptron"
        assert result.passed is True
        assert result.correct_count == 3
        assert result.total_questions == 4

    def test_score_quiz_fail(self):
        result = self.engine.score_quiz(
            knowledge_point_id="perceptron",
            total_questions=4,
            correct_answers=1,
        )
        assert result.mastery_level < 0.6
        assert result.passed is False

    def test_score_quiz_perfect(self):
        result = self.engine.score_quiz(
            knowledge_point_id="perceptron",
            total_questions=4,
            correct_answers=4,
        )
        assert result.mastery_level == 1.0
        assert result.passed is True
        assert "\u4f18\u79c0" in result.feedback

    def test_score_quiz_with_previous_attempts(self):
        r1 = self.engine.score_quiz("perceptron", 4, 3, previous_attempts=0)
        r2 = self.engine.score_quiz("perceptron", 4, 3, previous_attempts=1)
        assert r2.mastery_level >= r1.mastery_level

    def test_score_quiz_no_attempt_bonus_on_fail(self):
        r1 = self.engine.score_quiz("perceptron", 4, 1, previous_attempts=0)
        r2 = self.engine.score_quiz("perceptron", 4, 1, previous_attempts=5)
        assert r2.mastery_level == r1.mastery_level

    def test_score_quiz_zero_questions(self):
        result = self.engine.score_quiz("test", 0, 0)
        assert result.mastery_level == 0
        assert result.passed is False

    def test_mastery_capped_at_one(self):
        result = self.engine.score_quiz("test", 4, 4, previous_attempts=10)
        assert result.mastery_level <= 1.0