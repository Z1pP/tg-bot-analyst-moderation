import pickle
from typing import Optional, TypeVar

import redis.asyncio as redis

from .base import ICache

T = TypeVar("T")


class RedisCache(ICache):
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self.redis = redis.from_url(redis_url)
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Optional[T]:
        data = await self.redis.get(key)
        return pickle.loads(data) if data else None

    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        data = pickle.dumps(value)
        ttl = ttl or self.default_ttl
        await self.redis.set(key, data, ex=ttl)

    async def delete(self, key: str) -> bool:
        return bool(await self.redis.delete(key))

    async def clear(self) -> None:
        await self.redis.flushdb()
