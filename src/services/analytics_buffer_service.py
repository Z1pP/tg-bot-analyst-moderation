import logging
from typing import List, Type, TypeVar

import redis.asyncio as redis
from pydantic import BaseModel

from config import settings
from dto.buffer import BufferedMessageDTO, BufferedMessageReplyDTO, BufferedReactionDTO

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AnalyticsBufferService:
    """Сервис для буферизации сообщений и реакций в Redis"""

    REDIS_KEY_MESSAGES = "buffer:messages"
    REDIS_KEY_REACTIONS = "buffer:reactions"
    REDIS_KEY_REPLIES = "buffer:replies"

    def __init__(self, redis_url: str = None):
        self.redis_url = (
            redis_url
            or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        )
        self._redis: redis.Redis | None = None
        self._connected = False

    async def _ensure_connection(self) -> bool:
        """Устанавливает соединение с Redis если его нет"""
        if self._redis is None:
            try:
                self._redis = redis.from_url(self.redis_url, decode_responses=False)
                await self._redis.ping()
                self._connected = True
                logger.debug("Подключение к Redis установлено")
                return True
            except Exception as e:
                logger.error(f"Ошибка подключения к Redis: {e}")
                self._connected = False
                return False
        elif not self._connected:
            try:
                await self._redis.ping()
                self._connected = True
                return True
            except Exception as e:
                logger.error(f"Ошибка проверки соединения Redis: {e}")
                self._connected = False
                return False
        return True

    async def _add_to_buffer(self, key: str, dto: BaseModel, entity_name: str) -> None:
        """Общий метод для добавления DTO в буфер Redis"""
        if not await self._ensure_connection():
            logger.error(f"Redis недоступен, {entity_name} не добавлено в буфер")
            return

        try:
            json_data = dto.model_dump_json()
            await self._redis.rpush(key, json_data.encode("utf-8"))
            logger.debug(f"{entity_name.capitalize()} добавлено в буфер")
        except Exception as e:
            logger.error(
                f"Ошибка при добавлении {entity_name} в буфер: {e}", exc_info=True
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
                except Exception as e:
                    logger.error(f"Ошибка десериализации {entity_name}: {e}")
                    continue

            logger.debug(f"Прочитано {len(items)} {entity_name} из буфера")
            return items
        except Exception as e:
            logger.error(
                f"Ошибка при чтении {entity_name} из буфера: {e}", exc_info=True
            )
            return []

    async def _trim_buffer(self, key: str, count: int, entity_name: str) -> None:
        """Общий метод для удаления обработанных элементов из буфера Redis"""
        if not await self._ensure_connection():
            return

        try:
            await self._redis.ltrim(key, count, -1)
            logger.debug(f"Удалено {count} {entity_name} из буфера")
        except Exception as e:
            logger.error(
                f"Ошибка при удалении {entity_name} из буфера: {e}", exc_info=True
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
        """Закрывает соединение с Redis"""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.debug("Соединение с Redis закрыто")
