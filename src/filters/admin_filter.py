import logging
from typing import Optional

from aiogram.filters import Filter
from aiogram.types import InlineQuery, Message

from constants.enums import UserRole
from container import container
from models.user import User
from services.caching import ICache
from usecases.user import GetUserFromDatabaseUseCase

logger = logging.getLogger(__name__)


class BaseUserFilter(Filter):
    """Базовый фильтр для работы с пользователями"""

    def __init__(self):
        self._cache: ICache = container.resolve(ICache)

    async def get_user(self, username: str) -> Optional[User]:
        """Получает пользователя из кеша или БД"""
        user = self._cache.get(username)

        if not user:
            user = await self._get_user_from_db(username)
            if user:
                self._cache.set(username, user)

        return user

    async def _get_user_from_db(self, username: str) -> Optional[User]:
        """Получает пользователя из БД"""
        try:
            usecase = container.resolve(GetUserFromDatabaseUseCase)
            return await usecase.execute(username=username)
        except Exception:
            return None


class StaffOnlyFilter(BaseUserFilter):
    """Фильтр для всех ролей пользователей"""

    async def __call__(self, message: Message) -> bool:
        username = message.from_user.username
        if not username:
            return False

        user = await self.get_user(username)
        return user is not None


class AdminOnlyFilter(BaseUserFilter):
    """Фильтр только для администраторов"""

    async def __call__(self, message: Message) -> bool:
        username = message.from_user.username
        if not username:
            return False

        user = await self.get_user(username)
        return user is not None and user.role == UserRole.ADMIN


class StaffOnlyInlineFilter(BaseUserFilter):
    """Фильтр только для администраторов"""

    async def __call__(self, inline_query: InlineQuery) -> bool:
        username = inline_query.from_user.username
        if not username:
            return False

        user = await self.get_user(username)
        if not user:
            return False

        return user.role in (UserRole.ADMIN, UserRole.MODERATOR)
