import logging
from typing import List, Type, TypeVar

from pydantic import BaseModel
from redis.asyncio import Redis as RedisClient
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from dto.buffer import BufferedMessageDTO, BufferedMessageReplyDTO, BufferedReactionDTO

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_REDIS_ERRORS = (
    RedisConnectionError,
    RedisTimeoutError,
    OSError,
)


class AnalyticsBufferService:
    """Сервис для буферизации сообщений и реакций в Redis"""

    REDIS_KEY_MESSAGES = "buffer:messages"
    REDIS_KEY_REACTIONS = "buffer:reactions"
    REDIS_KEY_REPLIES = "buffer:replies"

    def __init__(self, redis_client: RedisClient) -> None:
        self._redis = redis_client
        self._connected = False

    async def _ensure_connection(self) -> bool:
        """Проверяет доступность Redis."""
        if not self._connected:
            try:
                await self._redis.ping()
                self._connected = True
                logger.debug("Подключение к Redis установлено")
                return True
            except _REDIS_ERRORS as e:
                logger.error("Ошибка подключения к Redis: %s", e)
                self._connected = False
                return False
        return True

    async def _add_to_buffer(self, key: str, dto: BaseModel, entity_name: str) -> None:
        """Общий метод для добавления DTO в буфер Redis"""
        if not await self._ensure_connection():
            logger.error("Redis недоступен, %s не добавлено в буфер", entity_name)
            return

        try:
            json_data = dto.model_dump_json()
            await self._redis.rpush(key, json_data.encode("utf-8"))
            logger.debug("%s добавлено в буфер", entity_name.capitalize())
        except _REDIS_ERRORS as e:
            logger.error(
                "Ошибка при добавлении %s в буфер: %s",
                entity_name,
                e,
                exc_info=True,
            )
        except (UnicodeEncodeError, TypeError) as e:
            logger.error(
                "Ошибка сериализации %s в буфер: %s",
                entity_name,
                e,
                exc_info=True,
            )

    async def _pop_from_buffer(
        self, key: str, dto_class: Type[T], count: int, entity_name: str
    ) -> List[T]:
        """Общий метод для получения пачки DTO из буфера Redis"""
        if not await self._ensure_connection():
            return []

        try:
            data = await self._redis.lrange(key, 0, count - 1)
            items = []
            for item in data:
                try:
                    json_str = item.decode("utf-8") if isinstance(item, bytes) else item
                    dto = dto_class.model_validate_json(json_str)
                    items.append(dto)
                except (ValueError, UnicodeDecodeError, TypeError) as e:
                    logger.error("Ошибка десериализации %s: %s", entity_name, e)
                    continue

            logger.debug("Прочитано %s %s из буфера", len(items), entity_name)
            return items
        except _REDIS_ERRORS as e:
            logger.error(
                "Ошибка при чтении %s из буфера: %s",
                entity_name,
                e,
                exc_info=True,
            )
            return []

    async def _trim_buffer(self, key: str, count: int, entity_name: str) -> None:
        """Общий метод для удаления обработанных элементов из буфера Redis"""
        if not await self._ensure_connection():
            return

        try:
            await self._redis.ltrim(key, count, -1)
            logger.debug("Удалено %s %s из буфера", count, entity_name)
        except _REDIS_ERRORS as e:
            logger.error(
                "Ошибка при удалении %s из буфера: %s",
                entity_name,
                e,
                exc_info=True,
            )

    async def add_message(self, dto: BufferedMessageDTO) -> None:
        """Добавляет сообщение в буфер Redis"""
        await self._add_to_buffer(self.REDIS_KEY_MESSAGES, dto, "сообщение")

    async def add_reaction(self, dto: BufferedReactionDTO) -> None:
        """Добавляет реакцию в буфер Redis"""
        await self._add_to_buffer(self.REDIS_KEY_REACTIONS, dto, "реакция")

    async def add_reply(self, dto: BufferedMessageReplyDTO) -> None:
        """Добавляет reply сообщение в буфер Redis"""
        await self._add_to_buffer(self.REDIS_KEY_REPLIES, dto, "reply")

    async def re_add_replies(self, dtos: List[BufferedMessageReplyDTO]) -> None:
        """Возвращает reply в буфер для повторной обработки."""
        if not dtos:
            return
        if not await self._ensure_connection():
            logger.error("Redis недоступен, reply не возвращены в буфер")
            return
        try:
            values = [dto.model_dump_json().encode("utf-8") for dto in dtos]
            await self._redis.rpush(self.REDIS_KEY_REPLIES, *values)
            logger.debug("Возвращено %d reply в буфер", len(dtos))
        except _REDIS_ERRORS as e:
            logger.error(
                "Ошибка при возврате reply в буфер: %s",
                e,
                exc_info=True,
            )
        except (UnicodeEncodeError, TypeError) as e:
            logger.error(
                "Ошибка сериализации reply при возврате в буфер: %s",
                e,
                exc_info=True,
            )

    async def pop_messages(self, count: int = 100) -> List[BufferedMessageDTO]:
        """Безопасно читает пачку сообщений из Redis без удаления."""
        return await self._pop_from_buffer(
            self.REDIS_KEY_MESSAGES, BufferedMessageDTO, count, "сообщений"
        )

    async def pop_reactions(self, count: int = 100) -> List[BufferedReactionDTO]:
        """Безопасно читает пачку реакций из Redis без удаления."""
        return await self._pop_from_buffer(
            self.REDIS_KEY_REACTIONS, BufferedReactionDTO, count, "реакций"
        )

    async def pop_replies(self, count: int = 100) -> List[BufferedMessageReplyDTO]:
        """Безопасно читает пачку reply сообщений из Redis без удаления."""
        return await self._pop_from_buffer(
            self.REDIS_KEY_REPLIES, BufferedMessageReplyDTO, count, "reply"
        )

    async def trim_messages(self, count: int) -> None:
        """Удаляет обработанные сообщения из Redis."""
        await self._trim_buffer(self.REDIS_KEY_MESSAGES, count, "сообщений")

    async def trim_reactions(self, count: int) -> None:
        """Удаляет обработанные реакции из Redis."""
        await self._trim_buffer(self.REDIS_KEY_REACTIONS, count, "реакций")

    async def trim_replies(self, count: int) -> None:
        """Удаляет обработанные reply сообщения из Redis."""
        await self._trim_buffer(self.REDIS_KEY_REPLIES, count, "reply")

    async def close(self) -> None:
        """Закрывает соединение с Redis. При использовании shared Redis — no-op."""
        self._connected = False
