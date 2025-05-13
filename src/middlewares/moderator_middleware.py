import logging
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache

from constants import ChatType
from container import container
from models import User
from usecases.user import GetUserFromDatabaseUseCase

logger = logging.getLogger(__name__)

TTL_SECONDS = 60 * 5  # 5 minutes


class ModeratorIdentityMiddleware(BaseMiddleware):
    def __init__(self):
        self._cache = TTLCache(maxsize=100, ttl=TTL_SECONDS)
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Filter what middleware work only with group and supergroup chats
        if not self._is_group_chat(event=event):
            return await handler(event, data)

        try:
            username = self._get_username(event=event)

            moderator = await self._get_moderator(username=username)
            if moderator:
                data["moderator"] = moderator

            return await handler(event, data)

        except Exception as e:
            logger.error("Error getting moderator: %s", str(e))
            return await handler(event, data)

    def _get_username(self, event: Message) -> str:
        return str(event.from_user.username)

    async def _get_moderator(self, username: str) -> Optional[User]:
        moderator = self._get_from_cache(username=username)
        if moderator:
            return moderator

        moderator = await self._get_moderator_from_database(username=username)
        if moderator:
            self._add_to_cache(username=username, moderator=moderator)

        return moderator

    async def _get_moderator_from_database(self, username: str) -> Optional[User]:
        usercase: GetUserFromDatabaseUseCase = container.resolve(
            GetUserFromDatabaseUseCase
        )
        return await usercase.execute(username=username)

    def _get_from_cache(self, username: str) -> Optional[User]:
        try:
            return self._cache.get(username)
        except Exception as e:
            logger.error("Error getting moderator from cache: %s", str(e))
            return None

    def _add_to_cache(self, username: str, moderator: User) -> None:
        self._cache[username] = moderator

    def _is_group_chat(self, event: Message) -> bool:
        chat_type = event.chat.type
        return chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]
