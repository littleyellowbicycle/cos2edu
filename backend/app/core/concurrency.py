import asyncio
from typing import Dict


class ConcurrencyLock:
    def __init__(self):
        self.locks: Dict[str, asyncio.Lock] = {}
    
    async def acquire(self, key: str) -> bool:
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        
        lock = self.locks[key]
        if lock.locked():
            return False
        
        await lock.acquire()
        return True
    
    async def release(self, key: str):
        if key in self.locks:
            lock = self.locks[key]
            if lock.locked():
                lock.release()


concurrency_lock = ConcurrencyLock()
