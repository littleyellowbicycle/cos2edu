from typing import Dict, Optional
from abc import ABC, abstractmethod
import asyncio
import time

from app.core.config import settings


class BaseConcurrencyLock(ABC):
    @abstractmethod
    async def acquire(self, key: str) -> bool:
        pass
    
    @abstractmethod
    async def release(self, key: str) -> None:
        pass
    
    @abstractmethod
    async def is_locked(self, key: str) -> bool:
        pass


class MemoryConcurrencyLock(BaseConcurrencyLock):
    def __init__(self):
        self._locks: Dict[str, bool] = {}
        self._lock_times: Dict[str, float] = {}
        self._lock_holders: Dict[str, int] = {}
        self._ttl: float = 300.0
        self._dict_lock = asyncio.Lock()
    
    async def acquire(self, key: str) -> bool:
        async with self._dict_lock:
            if key not in self._locks:
                self._locks[key] = False
                self._lock_holders[key] = None
            
            if self._locks[key]:
                return False
            
            self._locks[key] = True
            self._lock_times[key] = time.time()
            self._lock_holders[key] = id(asyncio.current_task())
        
        return True
    
    async def release(self, key: str) -> None:
        async with self._dict_lock:
            if key not in self._locks:
                return
            
            current_task_id = id(asyncio.current_task())
            if self._lock_holders.get(key) != current_task_id:
                raise RuntimeError("Cannot release lock held by another task")
            
            self._locks[key] = False
            self._lock_times[key] = time.time()
    
    async def is_locked(self, key: str) -> bool:
        async with self._dict_lock:
            return self._locks.get(key, False)
    
    async def cleanup_expired(self) -> None:
        async with self._dict_lock:
            current_time = time.time()
            expired_keys = [
                key for key, lock_time in self._lock_times.items()
                if current_time - lock_time > self._ttl
            ]
            for key in expired_keys:
                if key in self._locks:
                    del self._locks[key]
                if key in self._lock_times:
                    del self._lock_times[key]
                if key in self._lock_holders:
                    del self._lock_holders[key]


class RedisConcurrencyLock(BaseConcurrencyLock):
    def __init__(self, redis_url: str, ttl: int = 300):
        self._redis_url = redis_url
        self._ttl = ttl
        self._redis = None
        self._initialized = False
    
    async def _init_redis(self):
        if self._initialized:
            return
        
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(self._redis_url)
            self._initialized = True
        except ImportError:
            raise ImportError("Redis 未安装，请运行: pip install redis")
    
    async def acquire(self, key: str) -> bool:
        await self._init_redis()
        
        lock_key = f"concurrency:lock:{key}"
        
        result = await self._redis.set(
            lock_key,
            "1",
            ex=self._ttl,
            nx=True
        )
        
        return result is not None
    
    async def release(self, key: str) -> None:
        await self._init_redis()
        
        lock_key = f"concurrency:lock:{key}"
        await self._redis.delete(lock_key)
    
    async def is_locked(self, key: str) -> bool:
        await self._init_redis()
        
        lock_key = f"concurrency:lock:{key}"
        exists = await self._redis.exists(lock_key)
        return exists > 0


def get_concurrency_lock() -> BaseConcurrencyLock:
    if settings.RATE_LIMIT_STORAGE == "redis":
        redis_url = settings.REDIS_URL
        if not redis_url:
            if settings.REDIS_PASSWORD:
                redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
            else:
                redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        
        return RedisConcurrencyLock(redis_url=redis_url)
    
    return MemoryConcurrencyLock()


concurrency_lock = get_concurrency_lock()