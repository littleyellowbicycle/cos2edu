import os
import sys
from unittest.mock import patch, MagicMock

os.environ["APP_ENV"] = "test"

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.services.history_manager import (
    HistoryManager,
    HistoryTruncationResult,
    TokenCounter
)
from app.core.config import settings


class TestTokenCounterBoundary:
    
    def test_count_tokens_empty_string(self):
        result = TokenCounter.count_tokens("")
        
        assert result == 0
    
    def test_count_tokens_very_short(self):
        result = TokenCounter.count_tokens("a")
        
        assert result > 0
    
    def test_count_tokens_very_long_string(self):
        very_long_content = "你好" * 1000
        
        result = TokenCounter.count_tokens(very_long_content)
        
        assert result > 1000
        assert isinstance(result, int)
    
    def test_count_tokens_mixed_content(self):
        mixed_content = "Hello 你好 123 !@#" * 100
        
        result = TokenCounter.count_tokens(mixed_content)
        
        assert result > 0
        assert isinstance(result, int)
    
    def test_count_messages_tokens_empty(self):
        result = TokenCounter.count_messages_tokens([])
        
        assert result == 0
    
    def test_count_messages_tokens_many_messages(self):
        many_messages = [
            {"role": "user", "content": "测试内容" * 100},
            {"role": "assistant", "content": "回复内容" * 100}
        ] * 50
        
        result = TokenCounter.count_messages_tokens(many_messages)
        
        assert result > 0
        assert isinstance(result, int)


class TestHistoryManagerBoundary:
    
    def test_init_default_limits(self):
        manager = HistoryManager()
        
        assert manager.max_messages == settings.MAX_HISTORY_MESSAGES
        assert manager.max_tokens == settings.MAX_HISTORY_TOKENS
        assert manager.is_vip is False
    
    def test_init_vip_limits(self):
        manager = HistoryManager(is_vip=True)
        
        assert manager.max_messages == settings.MAX_HISTORY_MESSAGES_VIP
        assert manager.max_tokens == settings.MAX_HISTORY_TOKENS_VIP
        assert manager.is_vip is True
    
    def test_init_custom_limits(self):
        manager = HistoryManager(max_messages=10, max_tokens=1000)
        
        assert manager.max_messages == 10
        assert manager.max_tokens == 1000
        assert manager.is_vip is False
    
    def test_pair_messages_empty(self):
        manager = HistoryManager()
        
        result = manager._pair_messages([])
        
        assert result == []
    
    def test_pair_messages_single(self):
        manager = HistoryManager()
        messages = [{"role": "user", "content": "test"}]
        
        result = manager._pair_messages(messages)
        
        assert len(result) == 1
        assert len(result[0]) == 1
    
    def test_pair_messages_full_pair(self):
        manager = HistoryManager()
        messages = [
            {"role": "user", "content": "user 1"},
            {"role": "assistant", "content": "assistant 1"},
            {"role": "user", "content": "user 2"},
            {"role": "assistant", "content": "assistant 2"}
        ]
        
        result = manager._pair_messages(messages)
        
        assert len(result) == 2
        assert len(result[0]) == 2
        assert len(result[1]) == 2
    
    def test_pair_messages_odd_number(self):
        manager = HistoryManager()
        messages = [
            {"role": "user", "content": "user 1"},
            {"role": "assistant", "content": "assistant 1"},
            {"role": "user", "content": "user 2"}
        ]
        
        result = manager._pair_messages(messages)
        
        assert len(result) == 2
        assert len(result[0]) == 2
        assert len(result[1]) == 1


class TestHistoryManagerExtremeMessages:
    
    def test_very_long_user_message(self):
        manager = HistoryManager(max_messages=10, max_tokens=200)
        
        very_long_message = "这是一个非常长的消息。" * 100
        
        result = manager.build_optimized_messages(
            system_prompt="系统提示",
            history_messages=[],
            user_message=very_long_message
        )
        
        assert isinstance(result, HistoryTruncationResult)
        assert len(result.messages) == 2
        assert result.messages[0]["role"] == "system"
        assert result.messages[1]["role"] == "user"
    
    def test_system_prompt_exceeds_token_limit(self):
        manager = HistoryManager(max_messages=10, max_tokens=50)
        
        very_long_system = "系统提示" * 100
        
        result = manager.build_optimized_messages(
            system_prompt=very_long_system,
            history_messages=[],
            user_message="用户消息"
        )
        
        assert isinstance(result, HistoryTruncationResult)
        assert result.stats["truncated"] is True
        assert len(result.messages) == 2
    
    def test_many_history_messages(self):
        manager = HistoryManager(max_messages=4, max_tokens=1000)
        
        many_history = []
        for i in range(50):
            many_history.append({"role": "user", "content": f"用户消息 {i}"})
            many_history.append({"role": "assistant", "content": f"助手回复 {i}"})
        
        result = manager.build_optimized_messages(
            system_prompt="系统提示",
            history_messages=many_history,
            user_message="最终用户消息"
        )
        
        assert isinstance(result, HistoryTruncationResult)
        assert result.stats["truncated"] is True
        assert result.stats["original_history_count"] == 100
        assert result.stats["kept_history_count"] <= 4
        assert result.stats["removed_history_count"] >= 96
    
    def test_history_with_very_long_messages(self):
        manager = HistoryManager(max_messages=10, max_tokens=200)
        
        history_with_long_messages = [
            {"role": "user", "content": "很长的消息" * 50},
            {"role": "assistant", "content": "很长的回复" * 50}
        ] * 5
        
        result = manager.build_optimized_messages(
            system_prompt="系统提示",
            history_messages=history_with_long_messages,
            user_message="用户消息"
        )
        
        assert isinstance(result, HistoryTruncationResult)
        assert result.stats["total_tokens"] <= manager.max_tokens
    
    def test_no_history_just_system_and_user(self):
        manager = HistoryManager()
        
        result = manager.build_optimized_messages(
            system_prompt="你是一个助手",
            history_messages=[],
            user_message="你好"
        )
        
        assert isinstance(result, HistoryTruncationResult)
        assert len(result.messages) == 2
        assert result.stats["original_history_count"] == 0
        assert result.stats["kept_history_count"] == 0
        assert result.stats["truncated"] is False
    
    def test_build_messages_for_llm_simple(self):
        manager = HistoryManager()
        
        result = manager.build_messages_for_llm(
            system_prompt="系统提示",
            history_messages=[],
            user_message="用户消息"
        )
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
    
    def test_build_messages_for_llm_with_stats(self):
        manager = HistoryManager()
        
        messages, stats = manager.build_messages_for_llm(
            system_prompt="系统提示",
            history_messages=[],
            user_message="用户消息",
            return_stats=True
        )
        
        assert isinstance(messages, list)
        assert isinstance(stats, dict)
        assert "total_tokens" in stats
        assert "truncated" in stats
    
    def test_build_messages_for_llm_with_removed(self):
        manager = HistoryManager(max_messages=2, max_tokens=100)
        
        history = [
            {"role": "user", "content": "旧消息1"},
            {"role": "assistant", "content": "旧回复1"},
            {"role": "user", "content": "旧消息2"},
            {"role": "assistant", "content": "旧回复2"},
            {"role": "user", "content": "旧消息3"},
            {"role": "assistant", "content": "旧回复3"},
        ]
        
        messages, removed, stats = manager.build_messages_for_llm(
            system_prompt="系统提示",
            history_messages=history,
            user_message="新消息",
            return_removed=True
        )
        
        assert isinstance(messages, list)
        assert isinstance(removed, list)
        assert isinstance(stats, dict)
        assert len(removed) > 0 or stats["truncated"] is False


class TestHistorySummaryGeneratorBoundary:
    
    def test_format_history_empty(self):
        from app.services.history_manager import HistorySummaryGenerator
        
        result = HistorySummaryGenerator.format_history_for_summary([])
        
        assert result == ""
    
    def test_format_history_single_message(self):
        from app.services.history_manager import HistorySummaryGenerator
        
        messages = [{"role": "user", "content": "测试内容"}]
        
        result = HistorySummaryGenerator.format_history_for_summary(messages)
        
        assert "用户" in result
        assert "测试内容" in result
    
    def test_format_history_many_messages(self):
        from app.services.history_manager import HistorySummaryGenerator
        
        messages = []
        for i in range(10):
            messages.append({"role": "user", "content": f"用户消息 {i}"})
            messages.append({"role": "assistant", "content": f"助手回复 {i}"})
        
        result = HistorySummaryGenerator.format_history_for_summary(messages)
        
        assert len(result) > 0
        assert "用户消息 0" in result
        assert "助手回复 9" in result
    
    def test_format_history_unknown_role(self):
        from app.services.history_manager import HistorySummaryGenerator
        
        messages = [{"role": "system", "content": "系统消息"}]
        
        result = HistorySummaryGenerator.format_history_for_summary(messages)
        
        assert "system" in result


class TestExtremeTokenScenarios:
    
    def test_very_large_token_count(self):
        manager = HistoryManager(max_messages=1000, max_tokens=100000)
        
        huge_content = "中" * 10000
        
        history = []
        for i in range(100):
            history.append({"role": "user", "content": huge_content})
            history.append({"role": "assistant", "content": huge_content})
        
        result = manager.build_optimized_messages(
            system_prompt="系统提示",
            history_messages=history,
            user_message=huge_content
        )
        
        assert isinstance(result, HistoryTruncationResult)
        assert result.stats["original_history_count"] == 200
        assert result.stats["total_tokens"] <= manager.max_tokens
    
    def test_token_limit_exceeded_due_to_long_messages(self):
        manager = HistoryManager(max_messages=10, max_tokens=100)
        
        long_message = "这是一个很长的消息。" * 100
        
        result = manager.build_optimized_messages(
            system_prompt="系统提示",
            history_messages=[
                {"role": "user", "content": long_message},
                {"role": "assistant", "content": "回复"}
            ],
            user_message="新消息"
        )
        
        assert isinstance(result, HistoryTruncationResult)
        assert result.stats["truncated"] is True or result.stats["total_tokens"] <= manager.max_tokens
    
    def test_message_count_exceeds_limit(self):
        manager = HistoryManager(max_messages=4, max_tokens=10000)
        
        history = []
        for i in range(20):
            history.append({"role": "user", "content": f"消息 {i}"})
            history.append({"role": "assistant", "content": f"回复 {i}"})
        
        result = manager.build_optimized_messages(
            system_prompt="系统提示",
            history_messages=history,
            user_message="最终消息"
        )
        
        assert isinstance(result, HistoryTruncationResult)
        assert result.stats["original_history_count"] == 40
        assert result.stats["kept_history_count"] <= 4
        assert result.stats["truncated"] is True


class TestVIPvsRegularLimits:
    
    def test_vip_has_higher_limits(self):
        regular_manager = HistoryManager()
        vip_manager = HistoryManager(is_vip=True)
        
        assert vip_manager.max_messages >= regular_manager.max_messages
        assert vip_manager.max_tokens >= regular_manager.max_tokens
        assert vip_manager.is_vip is True
        assert regular_manager.is_vip is False
    
    def test_vip_allows_more_history(self):
        vip_manager = HistoryManager(is_vip=True)
        
        history = []
        for i in range(settings.MAX_HISTORY_MESSAGES_VIP):
            history.append({"role": "user", "content": f"消息 {i}"})
            if i % 2 == 1:
                history.append({"role": "assistant", "content": f"回复 {i}"})
        
        result = vip_manager.build_optimized_messages(
            system_prompt="系统提示",
            history_messages=history[:10],
            user_message="用户消息"
        )
        
        assert result.stats["is_vip"] is True
        assert result.stats["max_messages_limit"] == settings.MAX_HISTORY_MESSAGES_VIP
        assert result.stats["max_tokens_limit"] == settings.MAX_HISTORY_TOKENS_VIP


class TestEdgeCases:
    
    def test_history_with_empty_content(self):
        manager = HistoryManager()
        
        history = [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": ""},
            {"role": "user", "content": "正常消息"}
        ]
        
        result = manager.build_optimized_messages(
            system_prompt="系统提示",
            history_messages=history,
            user_message="用户消息"
        )
        
        assert isinstance(result, HistoryTruncationResult)
        assert len(result.messages) > 0
    
    def test_all_history_messages_removed_due_to_tokens(self):
        manager = HistoryManager(max_messages=100, max_tokens=50)
        
        huge_message = "非常长的消息内容" * 100
        
        result = manager.build_optimized_messages(
            system_prompt="系统提示",
            history_messages=[
                {"role": "user", "content": huge_message},
                {"role": "assistant", "content": huge_message}
            ],
            user_message="新消息"
        )
        
        assert isinstance(result, HistoryTruncationResult)
        assert result.stats["truncated"] is True
    
    def test_stats_contains_all_expected_fields(self):
        manager = HistoryManager()
        
        result = manager.build_optimized_messages(
            system_prompt="系统提示",
            history_messages=[
                {"role": "user", "content": "历史消息"},
                {"role": "assistant", "content": "历史回复"}
            ],
            user_message="用户消息"
        )
        
        expected_fields = [
            "original_history_count",
            "kept_history_count",
            "removed_history_count",
            "system_tokens",
            "history_tokens",
            "user_tokens",
            "total_tokens",
            "truncated",
            "truncation_reason",
            "is_vip",
            "max_messages_limit",
            "max_tokens_limit"
        ]
        
        for field in expected_fields:
            assert field in result.stats, f"Missing field: {field}"
