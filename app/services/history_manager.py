from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

TOKEN_BUFFER_RESERVE = 100


@dataclass
class HistoryTruncationResult:
    messages: List[Dict[str, str]] = field(default_factory=list)
    removed_messages: List[Dict[str, str]] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


class TokenCounter:
    """Token 计算器，支持多种计算方式"""

    _encoding_cache: Dict[str, Any] = {}

    @classmethod
    def _get_encoding(cls, model: str) -> Any:
        if model not in cls._encoding_cache:
            try:
                import tiktoken
                try:
                    encoding = tiktoken.encoding_for_model(model)
                except KeyError:
                    encoding = tiktoken.get_encoding("cl100k_base")
                cls._encoding_cache[model] = encoding
            except ImportError:
                logger.warning("tiktoken not installed, using character-based estimation")
                return None
        return cls._encoding_cache[model]

    @classmethod
    def count_tokens(
        cls,
        content: str,
        model: Optional[str] = None,
        use_tiktoken: Optional[bool] = None
    ) -> int:
        if not content:
            return 0

        should_use_tiktoken = use_tiktoken if use_tiktoken is not None else settings.USE_TIKTOKEN
        
        if should_use_tiktoken:
            encoding = cls._get_encoding(model or settings.TIKTOKEN_DEFAULT_MODEL)
            if encoding:
                try:
                    return len(encoding.encode(content))
                except Exception as e:
                    logger.debug(f"tiktoken encoding failed, falling back: {e}")

        return cls._estimate_tokens(content)

    @classmethod
    def _estimate_tokens(cls, content: str) -> int:
        chinese_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        ascii_alpha_count = sum(1 for c in content if c.isascii() and c.isalpha())
        other_count = len(content) - chinese_count - ascii_alpha_count

        chinese_tokens = chinese_count / settings.TOKEN_ESTIMATION_RATIO
        english_tokens = ascii_alpha_count / 4.0
        other_tokens = other_count / 2.0

        return max(1, int(chinese_tokens + english_tokens + other_tokens) + 2)

    @classmethod
    def count_messages_tokens(
        cls,
        messages: List[Dict[str, str]],
        model: Optional[str] = None
    ) -> int:
        total = 0
        for msg in messages:
            total += cls.count_tokens(msg.get("content", ""), model)
            total += cls.count_tokens(msg.get("role", ""), model)
        return total


class HistorySummaryGenerator:
    """历史消息摘要生成器"""

    SUMMARY_PROMPT_TEMPLATE = """请将以下对话历史进行简明总结，保留关键信息：

要求：
1. 总结长度控制在 200-300 字以内
2. 保持对话的核心主题、关键决策和重要上下文
3. 省略无关细节和重复内容
4. 使用简洁的语言

对话历史：
{history_content}

请生成总结："""

    @staticmethod
    def format_history(messages: List[Dict[str, str]]) -> str:
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            role_display = "用户" if role == "user" else "助手" if role == "assistant" else role
            lines.append(f"[{role_display}]: {content}")
        return "\n".join(lines)

    @staticmethod
    def format_history_for_summary(messages: List[Dict[str, str]]) -> str:
        return HistorySummaryGenerator.format_history(messages)

    @staticmethod
    async def generate_summary(
        messages: List[Dict[str, str]],
        model_config: Optional[Any] = None,
        db: Optional[Any] = None
    ) -> Optional[str]:
        if not messages or not settings.ENABLE_HISTORY_SUMMARY:
            return None

        if not model_config and db:
            from app.services.crud_services import ModelConfigService
            model_config = ModelConfigService.get_default(db)

        if not model_config:
            logger.warning("无法生成历史总结：缺少模型配置")
            return None

        try:
            history_content = HistorySummaryGenerator.format_history(messages)
            prompt = HistorySummaryGenerator.SUMMARY_PROMPT_TEMPLATE.format(
                history_content=history_content
            )

            from app.services.llm_providers import get_provider

            provider = get_provider(
                provider_name=model_config.provider,
                api_key=model_config.api_key,
                base_url=model_config.base_url
            )

            summary = await provider.chat(
                messages=[{"role": "user", "content": prompt}],
                model=model_config.model_name,
                temperature=settings.SUMMARY_TEMPERATURE,
                max_tokens=settings.SUMMARY_MAX_TOKENS
            )

            logger.info(f"历史总结生成成功，原始消息数: {len(messages)}")
            return summary.strip()

        except Exception as e:
            logger.error(f"生成历史总结失败: {e}", exc_info=True)
            return None


class HistoryManager:
    """对话历史管理器，用于控制发送给 LLM 的消息数量和 token 数量"""

    def __init__(
        self,
        max_messages: Optional[int] = None,
        max_tokens: Optional[int] = None,
        is_vip: bool = False
    ):
        if is_vip:
            self.max_messages = max_messages or settings.MAX_HISTORY_MESSAGES_VIP
            self.max_tokens = max_tokens or settings.MAX_HISTORY_TOKENS_VIP
        else:
            self.max_messages = max_messages or settings.MAX_HISTORY_MESSAGES
            self.max_tokens = max_tokens or settings.MAX_HISTORY_TOKENS
        
        self.is_vip = is_vip

    def count_tokens(self, content: str, model: Optional[str] = None) -> int:
        return TokenCounter.count_tokens(content, model)

    def count_messages_tokens(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> int:
        return TokenCounter.count_messages_tokens(messages, model)

    def _pair_messages(self, messages: List[Dict[str, str]]) -> List[List[Dict[str, str]]]:
        paired = []
        temp_pair = []
        
        for msg in messages:
            temp_pair.append(msg)
            if len(temp_pair) == 2:
                paired.append(temp_pair)
                temp_pair = []
        
        if temp_pair:
            paired.append(temp_pair)
        
        return paired

    def _build_messages_with_truncation(
        self,
        system_prompt: str,
        history_messages: List[Dict[str, str]],
        user_message: str,
        model: Optional[str] = None
    ) -> tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, Any]]:
        stats = {
            "original_history_count": len(history_messages),
            "kept_history_count": 0,
            "removed_history_count": 0,
            "system_tokens": 0,
            "history_tokens": 0,
            "user_tokens": 0,
            "total_tokens": 0,
            "truncated": False,
            "truncation_reason": "",
            "is_vip": self.is_vip,
            "max_messages_limit": self.max_messages,
            "max_tokens_limit": self.max_tokens,
        }

        system_tokens = self.count_tokens(system_prompt, model)
        user_tokens = self.count_tokens(user_message, model)

        stats["system_tokens"] = system_tokens
        stats["user_tokens"] = user_tokens

        reserved_tokens = system_tokens + user_tokens + TOKEN_BUFFER_RESERVE

        if reserved_tokens >= self.max_tokens:
            return (
                [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}],
                history_messages.copy(),
                {**stats, 
                    "total_tokens": reserved_tokens,
                    "truncated": True,
                    "truncation_reason": "system_prompt + user_message exceeds token limit"
                }
            )

        available_tokens = self.max_tokens - reserved_tokens

        paired_history = self._pair_messages(history_messages)

        max_pairs = self.max_messages // 2
        if max_pairs < 1:
            max_pairs = 1

        recent_pairs = paired_history[-max_pairs:]

        selected_pairs = []
        removed_pairs = []
        current_tokens = 0

        for pair in reversed(recent_pairs):
            pair_tokens = 0
            for msg in pair:
                pair_tokens += self.count_tokens(msg.get("content", ""), model)
                pair_tokens += self.count_tokens(msg.get("role", ""), model)
            
            if current_tokens + pair_tokens <= available_tokens:
                selected_pairs.insert(0, pair)
                current_tokens += pair_tokens
            else:
                removed_pairs.append(pair)
                stats["truncated"] = True
                stats["truncation_reason"] = "history exceeds token or message limit"

        old_pairs = paired_history[:-len(recent_pairs)] if len(paired_history) > len(recent_pairs) else []
        if old_pairs:
            for pair in old_pairs:
                removed_pairs.insert(0, pair)
            stats["truncated"] = True
            stats["truncation_reason"] = "history exceeds token or message limit"

        removed_messages = []
        for pair in removed_pairs:
            removed_messages.extend(pair)

        final_messages = [{"role": "system", "content": system_prompt}]
        
        kept_count = 0
        for pair in selected_pairs:
            for msg in pair:
                final_messages.append({"role": msg["role"], "content": msg["content"]})
                kept_count += 1
        
        final_messages.append({"role": "user", "content": user_message})

        stats["kept_history_count"] = kept_count
        stats["removed_history_count"] = len(removed_messages)
        stats["history_tokens"] = current_tokens
        stats["total_tokens"] = system_tokens + current_tokens + user_tokens

        return final_messages, removed_messages, stats

    def build_optimized_messages(
        self,
        system_prompt: str,
        history_messages: List[Dict[str, str]],
        user_message: str,
        model: Optional[str] = None
    ) -> HistoryTruncationResult:
        messages, removed_messages, stats = self._build_messages_with_truncation(
            system_prompt, history_messages, user_message, model
        )
        return HistoryTruncationResult(
            messages=messages,
            removed_messages=removed_messages,
            stats=stats
        )

    def build_messages_for_llm(
        self,
        system_prompt: str,
        history_messages: List[Dict[str, str]],
        user_message: str,
        model: Optional[str] = None,
        return_stats: bool = False,
        return_removed: bool = False
    ):
        result = self.build_optimized_messages(
            system_prompt,
            history_messages,
            user_message,
            model
        )

        if result.stats["truncated"]:
            logger.info(
                f"对话历史已截断 {result.stats['truncation_reason']}",
                extra={
                    "original_count": result.stats["original_history_count"],
                    "kept_count": result.stats["kept_history_count"],
                    "removed_count": result.stats["removed_history_count"],
                    "total_tokens": result.stats["total_tokens"],
                    "is_vip": result.stats["is_vip"],
                }
            )

        if return_removed:
            return result.messages, result.removed_messages, result.stats
        elif return_stats:
            return result.messages, result.stats
        return result.messages


history_manager = HistoryManager()


def get_history_manager(is_vip: bool = False) -> HistoryManager:
    if is_vip:
        return HistoryManager(is_vip=True)
    return history_manager
