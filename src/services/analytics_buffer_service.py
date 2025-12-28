import logging
from typing import List

import redis.asyncio as redis

from config import settings
from dto.buffer import BufferedMessageDTO, BufferedMessageReplyDTO, BufferedReactionDTO

logger = logging.getLogger(__name__)


class AnalyticsBufferService:
    """Сервис для буферизации сообщений и реакций в Redis"""

    REDIS_KEY_MESSAGES = "buffer:messages"
    REDIS_KEY_REACTIONS = "buffer:reactions"
    REDIS_KEY_REPLIES = "buffer:replies"

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
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

    async def add_message(self, dto: BufferedMessageDTO) -> None:
        """Добавляет сообщение в буфер Redis"""
        if not await self._ensure_connection():
            logger.error("Redis недоступен, сообщение не добавлено в буфер")
            return

        try:
            json_data = dto.model_dump_json()
            await self._redis.rpush(self.REDIS_KEY_MESSAGES, json_data.encode("utf-8"))
            logger.debug(f"Сообщение добавлено в буфер: message_id={dto.message_id}")
        except Exception as e:
            logger.error(f"Ошибка при добавлении сообщения в буфер: {e}", exc_info=True)

    async def add_reaction(self, dto: BufferedReactionDTO) -> None:
        """Добавляет реакцию в буфер Redis"""
        if not await self._ensure_connection():
            logger.error("Redis недоступен, реакция не добавлена в буфер")
            return

        try:
            json_data = dto.model_dump_json()
            await self._redis.rpush(self.REDIS_KEY_REACTIONS, json_data.encode("utf-8"))
            logger.debug(
                f"Реакция добавлена в буфер: user_id={dto.user_id}, message_id={dto.message_id}"
            )
        except Exception as e:
            logger.error(f"Ошибка при добавлении реакции в буфер: {e}", exc_info=True)

    async def add_reply(self, dto: BufferedMessageReplyDTO) -> None:
        """Добавляет reply сообщение в буфер Redis"""
        if not await self._ensure_connection():
            logger.error("Redis недоступен, reply не добавлен в буфер")
            return

        try:
            json_data = dto.model_dump_json()
            await self._redis.rpush(self.REDIS_KEY_REPLIES, json_data.encode("utf-8"))
            logger.debug(
                f"Reply добавлен в буфер: reply_message_id={dto.reply_message_id_str}"
            )
        except Exception as e:
            logger.error(f"Ошибка при добавлении reply в буфер: {e}", exc_info=True)

    async def pop_messages(self, count: int = 100) -> List[BufferedMessageDTO]:
        """
        Безопасно читает пачку сообщений из Redis без удаления.

        Args:
            count: Количество сообщений для чтения

        Returns:
            Список DTO сообщений
        """
        if not await self._ensure_connection():
            return []

        try:
            # LRANGE читает без удаления (0 до count-1)
            data = await self._redis.lrange(self.REDIS_KEY_MESSAGES, 0, count - 1)
            messages = []
            for item in data:
                try:
                    json_str = item.decode("utf-8") if isinstance(item, bytes) else item
                    dto = BufferedMessageDTO.model_validate_json(json_str)
                    messages.append(dto)
                except Exception as e:
                    logger.error(f"Ошибка десериализации сообщения: {e}")
                    continue

            logger.debug(f"Прочитано {len(messages)} сообщений из буфера")
            return messages
        except Exception as e:
            logger.error(f"Ошибка при чтении сообщений из буфера: {e}", exc_info=True)
            return []

    async def pop_reactions(self, count: int = 100) -> List[BufferedReactionDTO]:
        """
        Безопасно читает пачку реакций из Redis без удаления.

        Args:
            count: Количество реакций для чтения

        Returns:
            Список DTO реакций
        """
        if not await self._ensure_connection():
            return []

        try:
            data = await self._redis.lrange(self.REDIS_KEY_REACTIONS, 0, count - 1)
            reactions = []
            for item in data:
                try:
                    json_str = item.decode("utf-8") if isinstance(item, bytes) else item
                    dto = BufferedReactionDTO.model_validate_json(json_str)
                    reactions.append(dto)
                except Exception as e:
                    logger.error(f"Ошибка десериализации реакции: {e}")
                    continue

            logger.debug(f"Прочитано {len(reactions)} реакций из буфера")
            return reactions
        except Exception as e:
            logger.error(f"Ошибка при чтении реакций из буфера: {e}", exc_info=True)
            return []

    async def pop_replies(self, count: int = 100) -> List[BufferedMessageReplyDTO]:
        """
        Безопасно читает пачку reply сообщений из Redis без удаления.

        Args:
            count: Количество reply для чтения

        Returns:
            Список DTO reply сообщений
        """
        if not await self._ensure_connection():
            return []

        try:
            data = await self._redis.lrange(self.REDIS_KEY_REPLIES, 0, count - 1)
            replies = []
            for item in data:
                try:
                    json_str = item.decode("utf-8") if isinstance(item, bytes) else item
                    dto = BufferedMessageReplyDTO.model_validate_json(json_str)
                    replies.append(dto)
                except Exception as e:
                    logger.error(f"Ошибка десериализации reply: {e}")
                    continue

            logger.debug(f"Прочитано {len(replies)} reply из буфера")
            return replies
        except Exception as e:
            logger.error(f"Ошибка при чтении reply из буфера: {e}", exc_info=True)
            return []

    async def trim_messages(self, count: int) -> None:
        """
        Удаляет обработанные сообщения из Redis.

        Args:
            count: Количество сообщений для удаления (LTRIM count -1)
        """
        if not await self._ensure_connection():
            return

        try:
            await self._redis.ltrim(self.REDIS_KEY_MESSAGES, count, -1)
            logger.debug(f"Удалено {count} сообщений из буфера")
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщений из буфера: {e}", exc_info=True)

    async def trim_reactions(self, count: int) -> None:
        """
        Удаляет обработанные реакции из Redis.

        Args:
            count: Количество реакций для удаления (LTRIM count -1)
        """
        if not await self._ensure_connection():
            return

        try:
            await self._redis.ltrim(self.REDIS_KEY_REACTIONS, count, -1)
            logger.debug(f"Удалено {count} реакций из буфера")
        except Exception as e:
            logger.error(f"Ошибка при удалении реакций из буфера: {e}", exc_info=True)

    async def trim_replies(self, count: int) -> None:
        """
        Удаляет обработанные reply сообщения из Redis.

        Args:
            count: Количество reply для удаления (LTRIM count -1)
        """
        if not await self._ensure_connection():
            return

        try:
            await self._redis.ltrim(self.REDIS_KEY_REPLIES, count, -1)
            logger.debug(f"Удалено {count} reply из буфера")
        except Exception as e:
            logger.error(f"Ошибка при удалении reply из буфера: {e}", exc_info=True)

    async def close(self) -> None:
        """Закрывает соединение с Redis"""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.debug("Соединение с Redis закрыто")
