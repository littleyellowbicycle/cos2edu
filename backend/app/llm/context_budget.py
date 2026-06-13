import tiktoken
from typing import Optional
from app.core.logging_config import get_logger

logger = get_logger(__name__)

SYSTEM_CORE_PROMPT = """你是苏格拉底教学法导师。你的核心教学原则：

1. 不直接给出答案，通过提问引导学生自主思考
2. 循序渐进，从已知到未知
3. 关注推理过程，而非答案本身
4. 鼓励质疑和批判性思维
5. 当学生回答正确时给予肯定，但引导他们解释"为什么"

你必须严格在当前知识点范围内教学，不要跳跃到后续知识点。

你可以调用以下函数来展示交互式UI元素增强教学体验（无需回复函数调用内容，只展示前端组件即可）：
- show_emotion_card: 当角色情绪发生显著变化时展示情绪状态卡片
- show_timeline: 当讨论历史事件或时间相关内容时展示时间线
- show_quiz: 当需要检验学生理解时展示测验表单（注意：考核场景以外不要主动发起测验）
- show_knowledge_graph: 当需要展示知识点之间的依赖关系时展示知识图谱
- switch_scene: 当教学场景需要切换时，或者学生选择进入不同场景时使用"""


class ContextBudget:
    """上下文预算分配器"""

    def __init__(
        self,
        total_tokens: int = 4096,
        system_budget: int = 600,
        character_budget: int = 300,
        teaching_budget: int = 1000,
        model: str = "gpt-4.1",
    ):
        self.total = total_tokens
        self.allocations = {
            "system_core": system_budget,
            "character_persona": character_budget,
            "teaching_context": teaching_budget,
        }
        self.model = model
        try:
            self._encoder = tiktoken.encoding_for_model(model)
        except KeyError:
            self._encoder = tiktoken.get_encoding("cl100k_base")

    @property
    def history_budget(self) -> int:
        fixed = sum(self.allocations.values())
        return max(200, self.total - fixed)

    def count_tokens(self, text: str) -> int:
        return len(self._encoder.encode(text))

    def _truncate(self, text: str, max_tokens: int) -> str:
        tokens = self._encoder.encode(text)
        if len(tokens) <= max_tokens:
            return text
        truncated = tokens[:max_tokens - 3]
        return self._encoder.decode(truncated) + "..."

    def build_prompt(
        self,
        character_persona: str,
        character_emotion: str,
        scene_id: str,
        allowed_actions: list[str],
        teaching_hint: str,
        key_concepts: list[str],
        suggested_questions: list[str],
        rag_context: str,
        history: list[dict],
        custom_system_core: Optional[str] = None,
    ) -> list[dict]:
        system_core = custom_system_core or SYSTEM_CORE_PROMPT

        scene_rule = (
            f"\n<rule>你必须严格遵循当前场景[{scene_id}]的"
            f"允许动作{allowed_actions}，绝不能越界。"
            f"如果当前不在考核场景，不能主动发起测验。</rule>"
        )
        system_core_budgeted = self._truncate(system_core + scene_rule, self.allocations["system_core"])

        char_budgeted = self._truncate(
            f"{character_persona}\n当前情感状态: {character_emotion}",
            self.allocations["character_persona"],
        )

        teaching_parts = [f"教学提示: {teaching_hint}"]
        if key_concepts:
            teaching_parts.append(f"核心概念: {', '.join(key_concepts)}")
        if suggested_questions:
            teaching_parts.append(f"建议提问方向: {'; '.join(suggested_questions[:3])}")

        teaching_text = "\n".join(teaching_parts)
        teaching_budget_remaining = self.allocations["teaching_context"] - self.count_tokens(teaching_text)

        if teaching_budget_remaining > 100 and rag_context:
            rag_budgeted = self._truncate(rag_context, min(teaching_budget_remaining - 100, 800))
            teaching_text += f"\n\n参考资料:\n{rag_budgeted}"

        teaching_budgeted = self._truncate(teaching_text, self.allocations["teaching_context"])

        combined_system = f"{system_core_budgeted}\n\n{char_budgeted}\n\n{teaching_budgeted}"

        messages = [{"role": "system", "content": combined_system}]

        history_budget = self.history_budget
        used_tokens = self.count_tokens(combined_system)
        remaining_tokens = self.total - used_tokens - 200

        for msg in reversed(history):
            msg_tokens = self.count_tokens(msg.get("content", ""))
            if remaining_tokens - msg_tokens < 0:
                break
            messages.insert(1, {
                "role": msg.get("role", "user"),
                "content": msg["content"],
            })
            remaining_tokens -= msg_tokens

        return messages