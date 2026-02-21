import asyncio
import logging
import pickle
from typing import Optional, TypeVar

import redis.asyncio as redis
from redis.exceptions import (
    AuthenticationError,
    ConnectionError as RedisConnectionError,
    ResponseError,
    TimeoutError as RedisTimeoutError,
)

from .base import ICache

logger = logging.getLogger(__name__)
T = TypeVar("T")

_REDIS_ERRORS = (
    RedisConnectionError,
    OSError,
    ResponseError,
    RedisTimeoutError,
    asyncio.TimeoutError,
    AuthenticationError,
)


class RedisCache(ICache):
    def __init__(self, redis_url: str, default_ttl: int = 3600) -> None:
        self.redis = redis.from_url(redis_url)
        self.default_ttl = default_ttl
        self._connected = False

    async def _ensure_connection(self) -> bool:
        if not self._connected:
            try:
                await self.redis.ping()
                self._connected = True
            except _REDIS_ERRORS as e:
                self._connected = False
                if isinstance(e, AuthenticationError):
                    logger.error("Ошибка аутентификации Redis: %s", e)
                elif isinstance(e, (RedisConnectionError, OSError)):
                    logger.error("Ошибка подключения Redis: %s", e)
                elif isinstance(e, ResponseError):
                    logger.error("Ошибка ответа Redis: %s", e)
                elif isinstance(e, (RedisTimeoutError, asyncio.TimeoutError)):
                    logger.warning(
                        "Таймаут на соединение или выполнение команды Redis: %s",
                        e,
                    )
                else:
                    logger.error("Ошибка Redis: %s", e)
                return False
        return True

    async def get(self, key: str) -> Optional[T]:
        try:
            if not await self._ensure_connection():
                return None
            data = await self.redis.get(key)
            result = pickle.loads(data) if data else None
            logger.debug("Redis GET %s: %s", key, "HIT" if result else "MISS")
            return result
        except _REDIS_ERRORS as e:
            logger.error("Redis GET %s failed: %s", key, e)
            return None
        except (pickle.PickleError, TypeError, ValueError) as e:
            logger.error("Redis GET %s deserialize failed: %s", key, e)
            return None

    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        try:
            if not await self._ensure_connection():
                return
            data = pickle.dumps(value)
            ttl = ttl or self.default_ttl
            await self.redis.set(key, data, ex=ttl)
            logger.debug("Redis SET %s: OK (TTL: %ss)", key, ttl)
        except _REDIS_ERRORS as e:
            logger.error(f"Redis SET {key} failed: {e}")
        except (pickle.PickleError, TypeError) as e:
            logger.error(f"Redis SET {key} serialize failed: {e}")

    async def delete(self, key: str) -> bool:
        try:
            if not await self._ensure_connection():
                return False
            result = bool(await self.redis.delete(key))
            logger.debug(f"Redis DELETE {key}: {'OK' if result else 'NOT_FOUND'}")
            return result
        except _REDIS_ERRORS as e:
            logger.error("Redis DELETE %s failed: %s", key, e)
            return False

    async def clear(self) -> None:
        try:
            if not await self._ensure_connection():
                return
            await self.redis.flushdb()
            logger.debug("Redis CLEAR: OK")
        except _REDIS_ERRORS as e:
            logger.error("Redis CLEAR failed: %s", e)

    async def increment(self, key: str, ttl: Optional[int] = None) -> int:
        """
        Инкрементирует значение по ключу. Если ключа нет, создает его со значением 1.

        Args:
            key: Ключ для инкремента
            ttl: Время жизни в секундах (устанавливается только при создании ключа)

        Returns:
            Новое значение после инкремента
        """
        try:
            if not await self._ensure_connection():
                return 0
            # Используем INCR для атомарного инкремента
            value = await self.redis.incr(key)
            # Если значение стало 1 (ключ только что создан), устанавливаем TTL
            if value == 1 and ttl:
                await self.redis.expire(key, ttl)
            logger.debug(f"Redis INCR {key}: {value}")
            return value
        except _REDIS_ERRORS as e:
            logger.error("Redis INCR %s failed: %s", key, e)
            return 0

    async def exists(self, key: str) -> bool:
        """
        Проверяет существование ключа в Redis.

        Args:
            key: Ключ для проверки

        Returns:
            True если ключ существует, иначе False
        """
        try:
            if not await self._ensure_connection():
                return False
            result = bool(await self.redis.exists(key))
            logger.debug("Redis EXISTS %s: %s", key, result)
            return result
        except _REDIS_ERRORS as e:
            logger.error("Redis EXISTS %s failed: %s", key, e)
            return False
