import logging
from typing import Optional

from aiogram.filters import Filter
from aiogram.types import CallbackQuery, InlineQuery, Message, MessageReactionUpdated
from punq import Container

from constants.enums import UserRole
from models.user import User

logger = logging.getLogger(__name__)


class BaseUserFilter(Filter):
    """Базовый фильтр для работы с пользователями"""

    async def get_user(
        self, tg_id: str, current_username: str, container: Container
    ) -> Optional[User]:
        """Получает пользователя из кеша или БД через UserService"""
        from services.user.user_service import UserService

        user_service: UserService = container.resolve(UserService)
        return await user_service.get_user(tg_id=tg_id, username=current_username)


class AdminOnlyFilter(BaseUserFilter):
    async def __call__(
        self, event: Message | CallbackQuery, container: Container
    ) -> bool:
        if isinstance(event, Message):
            tg_id = str(event.from_user.id)
            current_username = event.from_user.username
        elif isinstance(event, CallbackQuery):
            tg_id = str(event.from_user.id)
            current_username = event.from_user.username
        else:
            return False

        user = await self.get_user(
            tg_id=tg_id, current_username=current_username, container=container
        )

        if user and user.role in (
            UserRole.ADMIN,
            UserRole.ROOT,
            UserRole.DEV,
            UserRole.OWNER,
        ):
            return True

        await event.answer("⛔ У Вас нет доступа к сервисам Analyst AI")


class StaffOnlyFilter(BaseUserFilter):
    async def __call__(self, message: Message, container: Container) -> bool:
        tg_id = str(message.from_user.id)
        current_username = message.from_user.username

        user = await self.get_user(
            tg_id=tg_id, current_username=current_username, container=container
        )
        return user.role in (UserRole.ADMIN, UserRole.MODERATOR)


class StaffOnlyInlineFilter(BaseUserFilter):
    """Фильтр только для администраторов"""

    async def __call__(self, inline_query: InlineQuery, container: Container) -> bool:
        tg_id = str(inline_query.from_user.id)
        current_username = inline_query.from_user.username

        user = await self.get_user(
            tg_id=tg_id, current_username=current_username, container=container
        )
        return user is not None and user.role in (UserRole.ADMIN, UserRole.MODERATOR)


class StaffOnlyReactionFilter(BaseUserFilter):
    """Фильтр только для администраторов"""

    async def __call__(
        self, event: MessageReactionUpdated, container: Container
    ) -> bool:
        tg_id = str(event.user.id)
        current_username = event.user.username

        user = await self.get_user(
            tg_id=tg_id, current_username=current_username, container=container
        )
        return user is not None and user.role in (UserRole.ADMIN, UserRole.MODERATOR)
