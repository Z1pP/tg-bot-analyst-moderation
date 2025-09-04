import asyncio
import logging
import pickle
from typing import Optional, TypeVar

import redis.asyncio as redis
from redis.exceptions import (
    AuthenticationError,
    ConnectionError,
    ResponseError,
    TimeoutError,
)

from .base import ICache

logger = logging.getLogger(__name__)
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
            except (ConnectionError, OSError) as e:
                self._connected = False
                logger.error(f"Ошибка подключения Redis: {e}")
                return False
            except AuthenticationError as e:
                self._connected = False
                logger.error(f"Ошибка аутентификации Redis: {e}")
                return False
            except ResponseError as e:
                self._connected = False
                logger.error(f"Ошибка ответа Redis: {e}")
                return False
            except (TimeoutError, asyncio.TimeoutError) as e:
                self._connected = False
                logger.warning(
                    f"Таймаут на соединение или выполнение команды Redis: {e}"
                )
                return False
            except Exception as e:
                self._connected = False
                logger.exception(f"Неожиданная ошибка Redis: {e}")
                return False
        return True

    async def get(self, key: str) -> Optional[T]:
        try:
            if not await self._ensure_connection():
                return None
            data = await self.redis.get(key)
            result = pickle.loads(data) if data else None
            logger.debug(f"Redis GET {key}: {'HIT' if result else 'MISS'}")
            return result
        except Exception as e:
            logger.error(f"Redis GET {key} failed: {e}")
            return None

    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        try:
            if not await self._ensure_connection():
                return
            data = pickle.dumps(value)
            ttl = ttl or self.default_ttl
            await self.redis.set(key, data, ex=ttl)
            logger.debug(f"Redis SET {key}: OK (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Redis SET {key} failed: {e}")

    async def delete(self, key: str) -> bool:
        try:
            if not await self._ensure_connection():
                return False
            result = bool(await self.redis.delete(key))
            logger.debug(f"Redis DELETE {key}: {'OK' if result else 'NOT_FOUND'}")
            return result
        except Exception as e:
            logger.error(f"Redis DELETE {key} failed: {e}")
            return False

    async def clear(self) -> None:
        try:
            if not await self._ensure_connection():
                return
            await self.redis.flushdb()
            logger.debug("Redis CLEAR: OK")
        except Exception as e:
            logger.error(f"Redis CLEAR failed: {e}")
