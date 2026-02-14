import logging

from aiogram.types import CallbackQuery, InlineQuery, Message
from punq import Container

from constants.enums import UserRole
from filters.base_filter import BaseUserFilter

logger = logging.getLogger(__name__)


class AdminOnlyFilter(BaseUserFilter):
    async def __call__(
        self,
        event: Message | CallbackQuery,
        container: Container,
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
        return user is not None and user.role in (
            UserRole.ADMIN,
            UserRole.MODERATOR,
            UserRole.DEV,
            UserRole.ROOT,
            UserRole.OWNER,
        )


class StaffOnlyInlineFilter(BaseUserFilter):
    """Фильтр только для администраторов"""

    async def __call__(self, inline_query: InlineQuery, container: Container) -> bool:
        tg_id = str(inline_query.from_user.id)
        current_username = inline_query.from_user.username

        user = await self.get_user(
            tg_id=tg_id, current_username=current_username, container=container
        )
        return user is not None and user.role in (
            UserRole.ADMIN,
            UserRole.MODERATOR,
            UserRole.DEV,
            UserRole.ROOT,
            UserRole.OWNER,
        )
