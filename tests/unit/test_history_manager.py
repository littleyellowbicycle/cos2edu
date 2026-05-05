import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.history_manager import (
    TokenCounter,
    HistoryManager,
    HistorySummaryGenerator,
    HistoryTruncationResult
)


class TestTokenCounter:
    
    def test_count_tokens_empty_string(self):
        assert TokenCounter.count_tokens("") == 0
    
    def test_count_tokens_chinese(self):
        with patch.object(TokenCounter, '_get_encoding', return_value=None):
            tokens = TokenCounter.count_tokens("你好世界")
            assert tokens > 0
    
    def test_count_tokens_english(self):
        with patch.object(TokenCounter, '_get_encoding', return_value=None):
            tokens = TokenCounter.count_tokens("Hello World")
            assert tokens > 0
    
    def test_count_messages_tokens(self):
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮助你的？"}
        ]
        with patch.object(TokenCounter, '_get_encoding', return_value=None):
            total = TokenCounter.count_messages_tokens(messages)
            assert total > 0


class TestHistoryManager:
    
    def test_init_default(self):
        manager = HistoryManager()
        assert manager.max_messages is not None
        assert manager.max_tokens is not None
        assert manager.is_vip is False
    
    def test_init_vip(self):
        manager = HistoryManager(is_vip=True)
        assert manager.is_vip is True
    
    def test_pair_messages_empty(self):
        manager = HistoryManager()
        paired = manager._pair_messages([])
        assert paired == []
    
    def test_pair_messages_single(self):
        manager = HistoryManager()
        messages = [{"role": "user", "content": "test"}]
        paired = manager._pair_messages(messages)
        assert len(paired) == 1
        assert len(paired[0]) == 1
    
    def test_pair_messages_full_pair(self):
        manager = HistoryManager()
        messages = [
            {"role": "user", "content": "user1"},
            {"role": "assistant", "content": "assistant1"},
            {"role": "user", "content": "user2"},
            {"role": "assistant", "content": "assistant2"}
        ]
        paired = manager._pair_messages(messages)
        assert len(paired) == 2
        assert len(paired[0]) == 2
        assert len(paired[1]) == 2
    
    def test_build_messages_for_llm_no_history(self):
        manager = HistoryManager(max_messages=10, max_tokens=4000)
        system_prompt = "你是一个助手"
        user_message = "你好"
        history_messages = []
        
        messages = manager.build_messages_for_llm(
            system_prompt,
            history_messages,
            user_message
        )
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
    
    def test_build_messages_for_llm_with_history(self):
        manager = HistoryManager(max_messages=10, max_tokens=4000)
        system_prompt = "你是一个助手"
        user_message = "新问题"
        history_messages = [
            {"role": "user", "content": "历史问题1"},
            {"role": "assistant", "content": "历史回答1"},
        ]
        
        messages = manager.build_messages_for_llm(
            system_prompt,
            history_messages,
            user_message
        )
        
        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[1]["content"] == "历史问题1"
        assert messages[2]["content"] == "历史回答1"
        assert messages[3]["content"] == "新问题"
    
    def test_build_optimized_messages_truncated_by_count(self):
        manager = HistoryManager(max_messages=2, max_tokens=4000)
        system_prompt = "你是一个助手"
        user_message = "新问题"
        
        history_messages = []
        for i in range(10):
            history_messages.append({"role": "user", "content": f"用户消息{i}"})
            history_messages.append({"role": "assistant", "content": f"助手消息{i}"})
        
        result = manager.build_optimized_messages(
            system_prompt,
            history_messages,
            user_message
        )
        
        assert isinstance(result, HistoryTruncationResult)
        assert len(result.removed_messages) > 0
        assert result.stats["truncated"] is True
    
    def test_build_messages_for_llm_with_stats(self):
        manager = HistoryManager(max_messages=10, max_tokens=4000)
        system_prompt = "你是一个助手"
        user_message = "你好"
        history_messages = []
        
        messages, stats = manager.build_messages_for_llm(
            system_prompt,
            history_messages,
            user_message,
            return_stats=True
        )
        
        assert isinstance(stats, dict)
        assert "total_tokens" in stats
    
    def test_build_messages_for_llm_with_removed(self):
        manager = HistoryManager(max_messages=2, max_tokens=4000)
        system_prompt = "你是一个助手"
        user_message = "新问题"
        
        history_messages = [
            {"role": "user", "content": "用户消息1"},
            {"role": "assistant", "content": "助手消息1"},
            {"role": "user", "content": "用户消息2"},
            {"role": "assistant", "content": "助手消息2"},
        ]
        
        messages, removed, stats = manager.build_messages_for_llm(
            system_prompt,
            history_messages,
            user_message,
            return_removed=True
        )
        
        assert isinstance(removed, list)


class TestHistorySummaryGenerator:
    
    def test_format_history(self):
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮助你的？"}
        ]
        
        formatted = HistorySummaryGenerator.format_history(messages)
        
        assert "[用户]" in formatted
        assert "[助手]" in formatted
        assert "你好" in formatted
    
    def test_format_history_empty(self):
        formatted = HistorySummaryGenerator.format_history([])
        assert formatted == ""
    
    @pytest.mark.asyncio
    async def test_generate_summary_no_messages(self):
        summary = await HistorySummaryGenerator.generate_summary([])
        assert summary is None
    
    @pytest.mark.asyncio
    async def test_generate_summary_disabled(self):
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"}
        ]
        
        with patch('app.core.config.settings.ENABLE_HISTORY_SUMMARY', False):
            summary = await HistorySummaryGenerator.generate_summary(messages)
            assert summary is None
