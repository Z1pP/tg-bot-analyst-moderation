import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache

from constants import ChatType
from container import container
from usecases.chat import GetOrCreateChatUseCase

logger = logging.getLogger(__name__)

TTL_SECONDS = 60 * 60  # 1 час для кеша чатов


class ChatSessionMiddleware(BaseMiddleware):
    """Middleware для работы с сессиями чатов"""

    def __init__(self):
        self._cache = TTLCache(maxsize=100, ttl=TTL_SECONDS)
        self._use_case: GetOrCreateChatUseCase = container.resolve(
            GetOrCreateChatUseCase
        )
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        try:
            # Проверяем что это групповой чат
            if not self._is_group_chat(event):
                return await handler(event, data)

            chat_id = str(event.chat.id)
            title = event.chat.title

            # Проверяем кеш
            chat = self._cache.get(chat_id)

            if not chat:
                # Если нет в кеше, получаем или создаем в БД
                chat = await self._use_case.execute(chat_id=chat_id, title=title)
                if chat:
                    self._cache[chat_id] = chat

            # Добавляем чат в data если нашли
            if chat:
                data["chat"] = chat
                return await handler(event, data)

        except Exception as e:
            logger.error(f"Error processing chat session: {e}")
            return await handler(event, data)

    @staticmethod
    def _is_group_chat(message: Message) -> bool:
        return message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
