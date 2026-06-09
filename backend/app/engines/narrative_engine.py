import json
from typing import Optional, AsyncIterator
from datetime import datetime

from app.graph.knowledge_graph import KnowledgeGraph
from app.engines.world_state_engine import WorldStateEngine
from app.engines.teaching_engine import TeachingEngine
from app.engines.character_engine import CharacterEngine
from app.engines.emotion_engine import EmotionEngine, EmotionUpdate
from app.engines.event_engine import EventEngine, TriggeredEvent
from app.engines.assessment_engine import AssessmentEngine, AssessmentResult, Quiz
from app.state.state_manager import StateManager
from app.services.chat_service import ChatService, LLMProvider
from app.engines.ui_orchestrator import UIOrchestrator
from app.services.rag_service import get_rag_service
from app.repositories.unit_of_work import UnitOfWork
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class NarrativeEngine:
    """叙事编排引擎：总调度，协调各引擎"""

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        world_state_engine: WorldStateEngine,
        character_engine: CharacterEngine,
        teaching_engine: TeachingEngine,
        state_manager: StateManager,
        emotion_engine: EmotionEngine = None,
        event_engine: EventEngine = None,
        assessment_engine: AssessmentEngine = None,
    ):
        self.graph = knowledge_graph
        self.world = world_state_engine
        self.characters = character_engine
        self.teaching = teaching_engine
        self.state_manager = state_manager
        self.emotion = emotion_engine
        self.events = event_engine
        self.assessment = assessment_engine or AssessmentEngine()
        self.rag = get_rag_service()
        self._ui_orchestrator = UIOrchestrator()
        self._message_counts: dict[int, int] = {}
        self._active_quizzes: dict[str, "Quiz"] = {}

    async def handle_chat_message(
        self,
        conversation_id: int,
        user_message: str,
        character_id: str,
        model_config=None,
    ) -> AsyncIterator[str]:
        """处理聊天消息，返回事件流 (以 JSON 行分隔)"""
        try:
            async with UnitOfWork() as uow:
                conversation = await uow.conversations.get_by_id(conversation_id)
                if not conversation:
                    raise ValueError(f"Conversation {conversation_id} not found")

                is_structured = (
                    conversation.material is not None
                    and conversation.material.status == "ready"
                )

                self._message_counts[conversation_id] = self._message_counts.get(conversation_id, 0) + 1

                point_data_for_prompt = None
                if is_structured:
                    mastered = await self._get_mastered_points(uow)
                    point_data_for_prompt = self.teaching.get_next_teaching_point(mastered)
                    if point_data_for_prompt and self.assessment and self.assessment.should_trigger_assessment(
                        point_id=point_data_for_prompt["point_id"],
                        mastered_points=mastered,
                        message_count=self._message_counts[conversation_id],
                    ):
                        yield json.dumps({
                            "type": "assessment.start",
                            "payload": {
                                "point_id": point_data_for_prompt["point_id"],
                                "point_name": point_data_for_prompt["name"],
                                "message": f"很好！我们已经讨论了「{point_data_for_prompt['name']}」的核心概念。让我们来做个小测验，检验一下你的理解。",
                            },
                        }, ensure_ascii=False)

                full_response = ""
                try:
                    rag_context = ""
                    try:
                        rag_ctx = self.rag.get_context(user_message, max_tokens=1500)
                        if rag_ctx:
                            rag_context = rag_ctx
                    except Exception:
                        pass

                    emotion_summary = ""
                    if self.emotion:
                        char_state = self.emotion.get_state(character_id)
                        if char_state:
                            emotion_summary = self._mood_to_description(char_state.mood)

                    async with UnitOfWork() as uow_inner:
                        from app.repositories.message_repository import MessageRepository
                        msg_repo = MessageRepository(uow_inner.session)
                        db_messages = await msg_repo.get_by_conversation(conversation_id)
                        history = [{"role": m.role, "content": m.content} for m in db_messages[-30:]]

                    prompt_messages = self._build_default_prompt(
                        character_id=character_id,
                        history=history,
                        rag_context=rag_context,
                        point_data=point_data_for_prompt,
                        emotion_summary=emotion_summary,
                    )
                    prompt_messages.append({"role": "user", "content": user_message})

                    from app.services.chat_service import LLMProvider
                    config_dict = None
                    if model_config:
                        config_dict = {
                            "provider": model_config.provider,
                            "model_name": model_config.model_name,
                            "api_key": model_config.api_key,
                            "base_url": model_config.base_url,
                            "group_id": getattr(model_config, "group_id", None),
                        }
                    llm = LLMProvider(config_dict)
                    tools = None
                    ui_orchestrator = getattr(self, '_ui_orchestrator', None)
                    if ui_orchestrator:
                        tools = ui_orchestrator.TOOL_DEFINITIONS

                    async for event in llm.chat_stream(prompt_messages, tools=tools):
                        if event["type"] == "text":
                            chunk = event["content"]
                            full_response += chunk
                            yield json.dumps({"type": "chat.token", "content": chunk}, ensure_ascii=False)
                        elif event["type"] == "tool_calls" and ui_orchestrator:
                            ui_components = ui_orchestrator.convert_tool_calls(event["tool_calls"])
                            if ui_components:
                                ui_msg = ui_orchestrator.build_ui_render_message(ui_components)
                                yield json.dumps(ui_msg, ensure_ascii=False)

                    async with UnitOfWork() as uow_save:
                        await uow_save.messages.create({
                            "conversation_id": conversation_id,
                            "role": "user",
                            "content": user_message,
                        })
                        await uow_save.messages.create({
                            "conversation_id": conversation_id,
                            "role": "assistant",
                            "content": full_response,
                        })
                except ValueError as e:
                    yield json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False)
                    return

                yield json.dumps({"type": "chat.complete", "content": full_response}, ensure_ascii=False)

                # Phase 1.5: Emotion update
                if self.emotion:
                    self._update_emotion_after_response(character_id, full_response, user_message)
                    emotion_update = self.emotion.update(character_id, "student_engaged", 0.05)
                    if emotion_update:
                        yield json.dumps({
                            "type": "emotion.update",
                            "payload": {
                                "character_id": character_id,
                                "mood": emotion_update.mood,
                                "mood_delta": emotion_update.mood_delta,
                                "cause": emotion_update.cause,
                                "expression": emotion_update.expression,
                            },
                        }, ensure_ascii=False)
                        await self.state_manager.update("mood_change", {
                            "character_id": int(character_id) if character_id.isdigit() else 1,
                            "mood": emotion_update.mood,
                        })

                # Phase 1.5: Check for events
                if self.events:
                    world_snap = self.world.get_full_snapshot()
                    mastered_set = mastered if is_structured else await self._get_mastered_points(uow)
                    char_states = {}
                    if self.emotion:
                        char_states = self.emotion.get_all_states()
                    event_list = self.events.check_time_events(world_snap.get("current_day", 1))
                    event_list += self.events.check_condition_events(
                        world_state=world_snap,
                        mastered_points=mastered_set,
                        character_states=char_states,
                    )
                    random_event = self.events.check_random_events()
                    if random_event:
                        event_list.append(random_event)
                    for event in event_list:
                        event_payload = {
                            "event_id": event.event_id,
                            "title": event.name,
                            "description": event.description,
                            "scene_change": event.scene_change,
                        }
                        if hasattr(event, "options") and event.options:
                            event_payload["options"] = event.options
                            narrative_choices_data = {
                                "event_id": event.event_id,
                                "title": event.name,
                                "description": event.description,
                                "options": event.options,
                            }
                            yield json.dumps({
                                "type": "narrative.options",
                                "payload": narrative_choices_data,
                            }, ensure_ascii=False)
                        yield json.dumps({
                            "type": "event.trigger",
                            "payload": event_payload,
                        }, ensure_ascii=False)
                        if event.scene_change:
                            new_scene = self.world.switch_scene(event.scene_change)
                            await self.state_manager.update("scene_change", {
                                "scene_id": event.scene_change,
                            })

        except Exception as e:
            logger.error(f"NarrativeEngine chat error: {e}", exc_info=True)
            yield json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False)

    async def handle_assessment_answer(
        self,
        conversation_id: int,
        point_id: str,
        answers: list[dict],
        character_id: str,
    ) -> dict:
        """处理考核答案，返回 AssessmentResult"""
        if not self.assessment:
            return {"error": "AssessmentEngine not initialized"}

        scores = []
        correct_count = 0
        for entry in answers:
            q = entry.get("question", {})
            a = entry.get("answer", "")
            if isinstance(a, str) and isinstance(q, dict):
                result = self.assessment.evaluate_answer(q, a)
                scores.append(result["score"])
                if result["is_correct"]:
                    correct_count += 1

        existing = await self._get_progress_for_point(point_id)
        attempts = (existing.get("attempts", 0) if existing else 0) + 1

        assessment_result = self.assessment.assess_point(
            point_id=point_id,
            scores=scores,
            attempts=attempts,
        )

        await self.state_manager.update("mastery_change", {
            "point_id": point_id,
            "mastery": assessment_result.mastery_level,
            "status": assessment_result.status,
        })

        if self.emotion:
            if assessment_result.passed:
                self.emotion.update(character_id, "student_correct", 0.08)
            else:
                self.emotion.update(character_id, "student_wrong", -0.03)

        return {
            "point_id": assessment_result.point_id,
            "passed": assessment_result.passed,
            "mastery_level": assessment_result.mastery_level,
            "status": assessment_result.status,
            "feedback": assessment_result.feedback,
            "score": assessment_result.score,
            "attempts": assessment_result.attempts,
        }

    async def generate_quiz(
        self,
        point_id: str,
        character_id: str,
        model_config=None,
    ) -> dict:
        """使用 LLM 生成考核题目"""
        point_meta = self.graph.get_point(point_id)
        if not point_meta:
            return {"error": f"Knowledge point {point_id} not found"}

        point_data = {
            "point_id": point_meta.id,
            "name": point_meta.name,
            "key_concepts": point_meta.key_concepts,
            "difficulty": point_meta.difficulty,
            "exercises": point_meta.exercises or [],
        }

        if not self.assessment:
            return {"error": "AssessmentEngine not initialized"}

        prompt = self.assessment.generate_quiz_prompt(point_data, character_id)

        try:
            async with UnitOfWork() as uow:
                config_obj = await uow.model_configs.get_default()
                if not config_obj:
                    return {"error": "No default model config"}

                config_dict = {
                    "provider": config_obj.provider,
                    "model_name": config_obj.model_name,
                    "api_key": config_obj.api_key,
                    "base_url": config_obj.base_url,
                    "group_id": getattr(config_obj, "group_id", None),
                }

            llm = LLMProvider(config_dict)
            messages = [{"role": "user", "content": prompt}]
            response = await llm.chat(messages)

            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            quiz_data = json.loads(response)
            return {
                "point_id": point_id,
                "point_name": point_meta.name,
                "quiz": quiz_data,
            }
        except json.JSONDecodeError as e:
            logger.error(f"Quiz generation JSON parse error: {e}")
            return {"error": "Failed to parse quiz from LLM response"}
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            return {"error": str(e)}

    def start_assessment(self, knowledge_point_id: str, num_questions: int = 4) -> "Quiz":
        point_meta = self.graph.get_point(knowledge_point_id)
        if not point_meta:
            raise ValueError(f"Knowledge point '{knowledge_point_id}' not found")

        point_data = {
            "id": point_meta.id,
            "name": point_meta.name,
            "difficulty": point_meta.difficulty,
            "key_concepts": point_meta.key_concepts,
            "suggested_questions": point_meta.suggested_questions,
            "exercises": point_meta.exercises,
        }

        quiz = self.assessment.generate_quiz(point_data, num_questions=num_questions)
        self._active_quizzes[knowledge_point_id] = quiz
        return quiz

    def submit_assessment_answer(
        self,
        knowledge_point_id: str,
        answers: list[int],
    ) -> "QuizResult":
        from app.engines.assessment_engine import QuizResult

        quiz = self._active_quizzes.get(knowledge_point_id)
        if not quiz:
            raise ValueError(f"No active quiz for knowledge point '{knowledge_point_id}'. Call start_assessment first.")

        correct = sum(
            1 for i, answer in enumerate(answers)
            if i < len(quiz.questions) and answer == quiz.questions[i].correct_answer
        )

        result = self.assessment.score_quiz(
            knowledge_point_id=knowledge_point_id,
            total_questions=len(quiz.questions),
            correct_answers=correct,
        )

        self._active_quizzes.pop(knowledge_point_id, None)

        return result

    def _mood_to_description(self, mood: float) -> str:
        if mood > 0.85:
            return "非常开心和兴奋"
        elif mood > 0.7:
            return "温和且专注"
        elif mood > 0.5:
            return "平静，略带思考"
        elif mood > 0.3:
            return "有些严肃"
        else:
            return "有些担心和不安"

    def _update_emotion_after_response(self, character_id: str, response: str, user_msg: str) -> None:
        """根据对话内容简单判断情感变化方向"""
        user_lower = user_msg.lower()
        positive_words = ["对", "是的", "正确", "明白了", "懂了", "谢谢", "yes", "right"]
        negative_words = ["不懂", "不理解", "错", "不会", "困难", "confused", "wrong"]

        has_positive = any(w in user_lower for w in positive_words)
        has_negative = any(w in user_lower for w in negative_words)

        if self.emotion:
            if has_positive:
                self.emotion.update(character_id, "student_correct", 0.05)
            elif has_negative:
                self.emotion.update(character_id, "student_wrong", -0.02)

    def _build_default_prompt(
        self,
        character_id: str,
        history: list[dict],
        rag_context: str = "",
        point_data: dict = None,
        emotion_summary: str = "",
    ) -> list[dict]:
        if point_data:
            scene = self.world.get_current_scene()
            return self.teaching.build_teaching_prompt(
                point_data=point_data,
                character_id=character_id,
                scene_id=scene.id,
                allowed_actions=scene.allowed_actions,
                emotion_summary=emotion_summary or self._mood_to_description(
                    self.emotion.get_state(character_id).mood if self.emotion and self.emotion.get_state(character_id) else 0.7
                ),
                history=history,
                rag_context=rag_context,
            )

        character = self.characters.get_character(character_id)
        system = "你是一位苏格拉底式教学助手，通过提问引导学生自主思考。"

        if character:
            system = f"{character.personality}\n背景: {character.background}"

        messages = [{"role": "system", "content": system}]
        if rag_context:
            messages.append({"role": "system", "content": f"参考资料:\n{rag_context[:2000]}"})

        messages.extend(history[-20:])
        return messages

    async def _get_mastered_points(self, uow) -> set[str]:
        from models.learning_progress import LearningProgress
        from sqlalchemy import select
        result = await uow.session.execute(
            select(LearningProgress).where(
                LearningProgress.status == "mastered"
            )
        )
        points = result.scalars().all()
        return {p.knowledge_point_id for p in points}

    async def _get_progress_for_point(self, point_id: str) -> Optional[dict]:
        try:
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
                        "mastery_level": progress.mastery_level,
                        "status": progress.status,
                        "attempts": progress.attempts,
                    }
        except Exception as e:
            logger.error(f"Failed to get progress for point {point_id}: {e}")
        return None

    async def get_full_snapshot(self) -> dict:
        """返回完整状态快照，用于 WS 重连对账"""
        world_snapshot = self.world.get_full_snapshot()

        characters_snapshot = {}
        if self.emotion:
            for cid, cdata in self.emotion.get_all_states().items():
                characters_snapshot[cid] = cdata
        else:
            async with UnitOfWork() as uow:
                from models.character_state import CharacterState
                from sqlalchemy import select
                result = await uow.session.execute(select(CharacterState))
                char_states = result.scalars().all()
                for cs in char_states:
                    char = self.characters.get_character(str(cs.character_id))
                    characters_snapshot[str(cs.character_id)] = {
                        "name": char.name if char else str(cs.character_id),
                        "mood": cs.current_mood,
                        "trust_level": cs.trust_level,
                    }

        async with UnitOfWork() as uow:
            mastered = await self._get_mastered_points(uow)
            all_points = self.graph.get_all_points()
            unlocked = self.graph.get_next_unlocked(mastered)

        current_point = unlocked[0] if unlocked else None
        point_meta = self.graph.get_point(current_point) if current_point else None

        return {
            "world": world_snapshot,
            "characters": characters_snapshot,
            "progress": {
                "currentPoint": current_point,
                "currentPointName": point_meta.name if point_meta else None,
                "status": "learning" if current_point else "completed",
                "mastery": 0,
                "completedPoints": len(mastered),
                "totalPoints": len(all_points),
                "masteredPoints": list(mastered),
                "next_point": unlocked[1] if len(unlocked) > 1 else None,
            },
            "activeEvents": [],
            "narrativeChoices": None,
        }

    async def activate_syllabus(self, material_id: int) -> dict:
        async with UnitOfWork() as uow:
            syllabus = await uow.syllabuses.get_by_material_id(material_id)
            if not syllabus:
                return {"error": f"Syllabus not found for material_id={material_id}"}

            content = syllabus.content or {}
            syllabus_name = content.get("course", {}).get("name", content.get("name", f"教材 {material_id}"))
            total_days = content.get("total_days", content.get("course", {}).get("total_days", 0))

        self.graph.load_from_syllabus_content(content)
        self.world.activate_syllabus(material_id, syllabus_name, total_days)

        return {
            "material_id": material_id,
            "syllabus_name": syllabus_name,
            "total_days": self.world._total_days,
            "knowledge_points": len(self.graph.get_all_points()),
            "modules": len(self.graph._module_order),
        }