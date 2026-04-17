import logging
from typing import List, Optional

from pydantic import ValidationError
from redis.asyncio import Redis as RedisClient
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from dto.automoderation import AutoModerationBufferItemDTO

logger = logging.getLogger(__name__)

_REDIS_ERRORS = (
    RedisConnectionError,
    RedisTimeoutError,
    OSError,
)

# RPUSH элемента; при длине списка >= threshold — LRANGE всех, DEL ключа, вернуть элементы; иначе nil.
_LUA_PUSH_AND_FLUSH = """
local key = KEYS[1]
local item = ARGV[1]
local threshold = tonumber(ARGV[2])
if threshold == nil or threshold < 1 then
  threshold = 1
end
redis.call('RPUSH', key, item)
local len = redis.call('LLEN', key)
if len >= threshold then
  local items = redis.call('LRANGE', key, 0, -1)
  redis.call('DEL', key)
  return items
end
return nil
"""


class AutoModerationBufferService:
    """Сервис списка сообщений на чат с атомарным сбросом при достижении порога."""

    def __init__(self, redis_client: RedisClient) -> None:
        self._redis = redis_client
        self._push_flush_script = self._redis.register_script(_LUA_PUSH_AND_FLUSH)

    def _key(self, chat_tgid: str) -> str:
        return f"automod:buffer:{chat_tgid}"

    async def append_text_message(
        self,
        chat_tgid: str,
        item: AutoModerationBufferItemDTO,
        batch_size: int,
    ) -> Optional[List[AutoModerationBufferItemDTO]]:
        """
        Добавляет текстовое сообщение в буфер чата.

        Если после добавления длина >= batch_size, атомарно возвращает всю пачку и очищает ключ.

        Returns:
            Список из batch_size элементов или None, если порог ещё не достигнут.
        """
        if batch_size < 1:
            logger.warning(
                "automod: batch_size=%s < 1 для chat_tgid=%s, используем 1",
                batch_size,
                chat_tgid,
            )
            batch_size = 1

        key = self._key(chat_tgid)
        try:
            raw = await self._push_flush_script(
                keys=[key],
                args=[item.model_dump_json(), str(batch_size)],
            )
        except _REDIS_ERRORS as e:
            logger.error(
                "automod Redis: ошибка append для chat_tgid=%s: %s",
                chat_tgid,
                e,
                exc_info=True,
            )
            return None
        except (TypeError, ValueError) as e:
            logger.error(
                "automod Redis: ошибка аргументов Lua для chat_tgid=%s: %s",
                chat_tgid,
                e,
                exc_info=True,
            )
            return None

        if raw is None:
            return None

        result: List[AutoModerationBufferItemDTO] = []
        for entry in raw:
            try:
                json_str = entry.decode("utf-8") if isinstance(entry, bytes) else entry
                result.append(AutoModerationBufferItemDTO.model_validate_json(json_str))
            except (UnicodeDecodeError, ValidationError, ValueError, TypeError) as e:
                logger.error(
                    "automod: не удалось десериализовать элемент буфера chat_tgid=%s: %s",
                    chat_tgid,
                    e,
                    exc_info=True,
                )
        if len(result) != len(raw):
            logger.warning(
                "automod: часть элементов буфера не распарсилась chat_tgid=%s",
                chat_tgid,
            )
        # Ключ уже очищен в Lua — возвращаем список (возможно пустой), не None
        return result
