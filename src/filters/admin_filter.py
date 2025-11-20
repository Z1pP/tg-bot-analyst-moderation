import logging
from typing import Optional

from aiogram.filters import Filter
from aiogram.types import CallbackQuery, InlineQuery, Message, MessageReactionUpdated

from constants.enums import UserRole
from container import container
from models.user import User
from repositories import UserRepository
from services.caching import ICache

logger = logging.getLogger(__name__)


class BaseUserFilter(Filter):
    """Базовый фильтр для работы с пользователями"""

    def __init__(self):
        self._cache: Optional[ICache] = None

    async def get_user(self, tg_id: str, current_username: str) -> Optional[User]:
        """Получает пользователя из кеша или БД с проверкой username"""
        if self._cache is None:
            self._cache = container.resolve(ICache)

        user = await self._cache.get(key=tg_id)

        if not user:
            user = await self._get_user_from_db(tg_id=tg_id)
            if user:
                await self._cache.set(key=tg_id, value=user)

        # Проверяем username
        if user and current_username and user.username != current_username:
            user = await self._update_username(
                user=user,
                new_username=current_username,
                tg_id=tg_id,
            )

        return user

    async def _get_user_from_db(self, tg_id: str) -> Optional[User]:
        try:
            user_repo: UserRepository = container.resolve(UserRepository)
            return await user_repo.get_user_by_tg_id(tg_id=tg_id)
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя из БД: {e}")

    async def _update_username(self, user: User, new_username: str, tg_id: str) -> User:
        """Обновляет username в БД и кеше только при изменении"""
        try:
            user_repo: UserRepository = container.resolve(UserRepository)
            updated_user = await user_repo.update_username(
                user_id=user.id,
                new_username=new_username,
            )

            # Обновляем кеш только если обновление прошло успешно
            if updated_user:
                await self._cache.set(key=tg_id, value=updated_user)
                logger.info(
                    f"Обновлен username для tg_id={tg_id}: {user.username} → {new_username}"
                )
                return updated_user

            return user
        except Exception as e:
            logger.error(f"Ошибка обновления username для tg_id={tg_id}: {e}")
            return user


class AdminOnlyFilter(BaseUserFilter):
    async def __call__(self, event: Message | CallbackQuery, *args, **kwds) -> bool:
        if isinstance(event, Message):
            tg_id = str(event.from_user.id)
            current_username = event.from_user.username
        elif isinstance(event, CallbackQuery):
            tg_id = str(event.from_user.id)
            current_username = event.from_user.username
        else:
            return False

        user = await self.get_user(tg_id=tg_id, current_username=current_username)
        return user is not None and user.role == UserRole.ADMIN


class StaffOnlyFilter(BaseUserFilter):
    async def __call__(self, message: Message) -> bool:
        tg_id = str(message.from_user.id)
        current_username = message.from_user.username

        user = await self.get_user(tg_id=tg_id, current_username=current_username)
        return user.role in (UserRole.ADMIN, UserRole.MODERATOR)


class StaffOnlyInlineFilter(BaseUserFilter):
    """Фильтр только для администраторов"""

    async def __call__(self, inline_query: InlineQuery) -> bool:
        tg_id = str(inline_query.from_user.id)
        current_username = inline_query.from_user.username

        user = await self.get_user(tg_id=tg_id, current_username=current_username)
        return user is not None and user.role in (UserRole.ADMIN, UserRole.MODERATOR)


class StaffOnlyReactionFilter(BaseUserFilter):
    """Фильтр только для администраторов"""

    async def __call__(self, event: MessageReactionUpdated) -> bool:
        tg_id = str(event.user.id)
        current_username = event.user.username

        user = await self.get_user(tg_id=tg_id, current_username=current_username)
        return user is not None and user.role in (UserRole.ADMIN, UserRole.MODERATOR)
