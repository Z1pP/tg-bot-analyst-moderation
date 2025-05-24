import logging
from typing import Optional

from aiogram.filters import Filter
from aiogram.types import Message
from cachetools import TTLCache

from constants.enums import UserRole
from container import container
from models.user import User
from usecases.user import GetUserFromDatabaseUseCase

logger = logging.getLogger(__name__)

TTL_SECONDS = 60  # 1 минута


class AdminOnlyFilter(Filter):
    def __init__(self):
        self._cache = TTLCache(maxsize=100, ttl=TTL_SECONDS)
        super().__init__()

    async def __call__(self, message: Message):
        username = self._get_username(message=message)

        user = self._get_user_from_cache(username=username)

        if not user:
            user = await self._get_from_database(username=username)

        if not user:
            # Игнорируем сообщение от пользователя если нет в БД
            return False

        if not self._is_admin(user=user):
            # Игнорируем сообщение от пользователя если не админ
            return False

        # Добавляем user в кеш
        self.add_user_to_cache(username=username, user=user)

        return True

    def _get_username(self, message: Message) -> str:
        return message.from_user.username

    def _get_user_from_cache(self, username: str) -> Optional[User]:
        try:
            return self._cache.get(username)
        except Exception as e:
            logger.error(
                "Error getting user from cache in %s.%s: %s",
                self.__class__.__name__,
                self._get_user_from_cache.__name__,
                str(e),
                exc_info=True,
            )
            return None

    def add_user_to_cache(self, username: str, user: User) -> None:
        try:
            self._cache[username] = user
        except Exception as e:
            logger.error(
                "Error adding user to cache in %s.%s: %s",
                self.__class__.__name__,
                self.add_user_to_cache.__name__,
                str(e),
                exc_info=True,
            )

    async def _get_from_database(self, username: str) -> Optional[User]:
        try:
            usercase: GetUserFromDatabaseUseCase = container.resolve(
                GetUserFromDatabaseUseCase
            )
            return await usercase.execute(username=username)
        except Exception:
            return None

    def _is_admin(self, user: User) -> bool:
        return user.role == UserRole.ADMIN
