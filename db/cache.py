import json
import os
import time
import asyncio
import aiofiles
from typing import Optional, Any

class AsyncCache:
    def __init__(self, filename: str = "cache.json", ttl: int = 3600):
        self.filename = filename
        self.ttl = ttl
        self.cache = {}
        self._lock = asyncio.Lock()
        self._load_sync()

    def _load_sync(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}

    async def _save(self):
        async with aiofiles.open(self.filename, 'w') as f:
            await f.write(json.dumps(self.cache))

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self.cache:
                item = self.cache[key]
                if time.time() - item['timestamp'] < self.ttl:
                    return item['data']
                else:
                    del self.cache[key]
                    await self._save()
            return None

    async def set(self, key: str, value: Any):
        async with self._lock:
            self.cache[key] = {
                'data': value,
                'timestamp': time.time()
            }
            await self._save()

    async def clear(self):
        async with self._lock:
            self.cache = {}
            await self._save()

    def get_stats(self):
        return {
            "total_keys": len(self.cache),
            "keys": list(self.cache.keys())
        }
