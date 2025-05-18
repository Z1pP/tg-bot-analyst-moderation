import logging
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache

from constants.enums import ChatType
from container import container
from models import User
from models.user import UserRole
from usecases.user import GetUserFromDatabaseUseCase

logger = logging.getLogger(__name__)

TTL_SECONDS = 60 * 5  # 5 minutes


class UserIdentityMiddleware(BaseMiddleware):
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

            user = await self._get_user(username=username)

            # Игнорирует сообщение если пользователь не найден в БД
            if not user:
                logger.warning("User not found in database: %s", username)
                return

            # Игнорирует сообщение если пользователь не является модератором или администратором
            if not self._is_moderator_or_admin(user=user):
                logger.warning("User is not a moderator or admin: %s", username)
                return

            data["sender"] = user
            return await handler(event, data)

        except Exception as e:
            logger.error("Error getting user: %s", str(e))
            return await handler(event, data)

    def _get_username(self, event: Message) -> str:
        return str(event.from_user.username)

    async def _get_user(self, username: str) -> Optional[User]:
        user = self._get_from_cache(username=username)
        if user:
            return user

        user = await self._get_user_from_database(username=username)
        if user:
            self._add_to_cache(username=username, user=user)

        return user

    async def _get_user_from_database(self, username: str) -> Optional[User]:
        usercase: GetUserFromDatabaseUseCase = container.resolve(
            GetUserFromDatabaseUseCase
        )
        return await usercase.execute(username=username)

    def _get_from_cache(self, username: str) -> Optional[User]:
        try:
            return self._cache.get(username)
        except Exception as e:
            logger.error("Error getting user from cache: %s", str(e))
            return None

    def _add_to_cache(self, username: str, user: User) -> None:
        self._cache[username] = user

    def _is_moderator_or_admin(self, user: User) -> bool:
        return user.role == UserRole.MODERATOR or user.role == UserRole.ADMIN

    def _is_group_chat(self, event: Message) -> bool:
        chat_type = event.chat.type
        return chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]
