import os
import sys
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

os.environ["APP_ENV"] = "test"

import pytest
from sqlalchemy.orm import Session

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.core.concurrency import (
    MemoryConcurrencyLock,
    BaseConcurrencyLock
)


class TestMemoryConcurrencyLock:
    
    @pytest.fixture(scope="function")
    def lock(self):
        return MemoryConcurrencyLock()
    
    @pytest.mark.asyncio
    async def test_acquire_new_lock(self, lock: MemoryConcurrencyLock):
        result = await lock.acquire("test-key")
        
        assert result is True
        assert await lock.is_locked("test-key") is True
    
    @pytest.mark.asyncio
    async def test_acquire_already_locked(self, lock: MemoryConcurrencyLock):
        await lock.acquire("test-key")
        
        result = await lock.acquire("test-key")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_release_lock(self, lock: MemoryConcurrencyLock):
        await lock.acquire("test-key")
        
        await lock.release("test-key")
        
        assert await lock.is_locked("test-key") is False
        assert "test-key" in lock._locks
        assert lock._locks["test-key"] is False
    
    @pytest.mark.asyncio
    async def test_release_nonexistent_lock(self, lock: MemoryConcurrencyLock):
        await lock.release("nonexistent-key")
        
        assert await lock.is_locked("nonexistent-key") is False
    
    @pytest.mark.asyncio
    async def test_is_locked_false_for_new_key(self, lock: MemoryConcurrencyLock):
        result = await lock.is_locked("new-key")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_multiple_locks_different_keys(self, lock: MemoryConcurrencyLock):
        await lock.acquire("key-1")
        await lock.acquire("key-2")
        
        assert await lock.is_locked("key-1") is True
        assert await lock.is_locked("key-2") is True
        
        await lock.release("key-1")
        
        assert await lock.is_locked("key-1") is False
        assert await lock.is_locked("key-2") is True
        
        await lock.release("key-2")
    
    @pytest.mark.asyncio
    async def test_concurrent_attempts_same_key(self, lock: MemoryConcurrencyLock):
        results = []
        release_event = asyncio.Event()
        
        async def attempt_and_hold(key, index):
            result = await lock.acquire(key)
            results.append((index, result))
            if result:
                await release_event.wait()
                await lock.release(key)
            return result
        
        acquire_1 = asyncio.create_task(attempt_and_hold("concurrent-key", 1))
        acquire_2 = asyncio.create_task(attempt_and_hold("concurrent-key", 2))
        
        await asyncio.sleep(0.01)
        
        release_event.set()
        
        result_1 = await acquire_1
        result_2 = await acquire_2
        
        assert (result_1 is True and result_2 is False) or (result_1 is False and result_2 is True)
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self, lock: MemoryConcurrencyLock):
        import time
        
        lock._ttl = 0.1
        
        await lock.acquire("expiring-key")
        
        assert await lock.is_locked("expiring-key") is True
        assert "expiring-key" in lock._lock_times
        
        await asyncio.sleep(0.2)
        
        await lock.cleanup_expired()
        
        assert await lock.is_locked("expiring-key") is False
        assert "expiring-key" not in lock._lock_times
        assert "expiring-key" not in lock._locks
    
    @pytest.mark.asyncio
    async def test_lock_ttl_initialization(self):
        lock = MemoryConcurrencyLock()
        
        assert lock._ttl == 300.0
        assert lock._locks == {}
        assert lock._lock_times == {}
        assert lock._lock_holders == {}
    
    @pytest.mark.asyncio
    async def test_release_unlocked_lock(self, lock: MemoryConcurrencyLock):
        await lock.acquire("test-key")
        await lock.release("test-key")
        
        await lock.release("test-key")
        
        assert await lock.is_locked("test-key") is False
    
    @pytest.mark.asyncio
    async def test_concurrent_acquire_race_condition(self, lock: MemoryConcurrencyLock):
        results = []
        
        async def attempt_acquire(key):
            result = await lock.acquire(key)
            results.append(result)
            if result:
                await asyncio.sleep(0.01)
                await lock.release(key)
        
        tasks = [asyncio.create_task(attempt_acquire("race-key")) for _ in range(10)]
        await asyncio.gather(*tasks)
        
        assert sum(results) == 1
    
    @pytest.mark.asyncio
    async def test_lock_cleanup_after_release(self, lock: MemoryConcurrencyLock):
        await lock.acquire("test-key")
        assert "test-key" in lock._locks
        
        await lock.release("test-key")
        assert "test-key" in lock._locks
        assert lock._locks["test-key"] is False
        assert "test-key" in lock._lock_times


class TestBaseConcurrencyLock:
    
    def test_abstract_class_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseConcurrencyLock()


class TestConcurrencyLockIntegration:
    
    @pytest.mark.asyncio
    async def test_lock_lifecycle(self):
        lock = MemoryConcurrencyLock()
        
        assert await lock.is_locked("lifecycle-key") is False
        
        result = await lock.acquire("lifecycle-key")
        assert result is True
        assert await lock.is_locked("lifecycle-key") is True
        
        result2 = await lock.acquire("lifecycle-key")
        assert result2 is False
        
        await lock.release("lifecycle-key")
        assert await lock.is_locked("lifecycle-key") is False
        
        result3 = await lock.acquire("lifecycle-key")
        assert result3 is True
        
        await lock.release("lifecycle-key")
    
    @pytest.mark.asyncio
    async def test_concurrent_stream_simulation(self):
        lock = MemoryConcurrencyLock()
        key = "stream:client-1:conv-123"
        
        async def long_stream_request(key, duration, release_event):
            acquired = await lock.acquire(key)
            if acquired:
                await asyncio.sleep(duration)
                await lock.release(key)
                release_event.set()
            return acquired
        
        async def quick_stream_attempt(key):
            return await lock.acquire(key)
        
        release_event = asyncio.Event()
        
        long_task = asyncio.create_task(long_stream_request(key, 0.1, release_event))
        await asyncio.sleep(0.01)
        
        quick_result = await quick_stream_attempt(key)
        
        assert quick_result is False
        
        await release_event.wait()
        await long_task
        
        final_result = await lock.acquire(key)
        assert final_result is True
        
        await lock.release(key)