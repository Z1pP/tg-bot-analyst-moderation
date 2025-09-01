import pickle
from typing import Optional, TypeVar

import redis.asyncio as redis

from .base import ICache

T = TypeVar("T")


class RedisCache(ICache):
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self.redis = redis.from_url(redis_url)
        self.default_ttl = default_ttl
        self._connected = False

    async def _ensure_connection(self) -> bool:
        if not self._connected:
            try:
                await self.redis.ping()
                self._connected = True
            except Exception:
                return False
        return True

    async def get(self, key: str) -> Optional[T]:
        try:
            if not await self._ensure_connection():
                return None
            data = await self.redis.get(key)
            return pickle.loads(data) if data else None
        except Exception:
            return None

    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        try:
            if not await self._ensure_connection():
                return
            data = pickle.dumps(value)
            ttl = ttl or self.default_ttl
            await self.redis.set(key, data, ex=ttl)
        except Exception:
            pass

    async def delete(self, key: str) -> bool:
        try:
            if not await self._ensure_connection():
                return False
            return bool(await self.redis.delete(key))
        except Exception:
            return False

    async def clear(self) -> None:
        try:
            if not await self._ensure_connection():
                return
            await self.redis.flushdb()
        except Exception:
            pass
