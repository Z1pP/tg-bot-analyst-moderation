from aiogram.types import CallbackQuery, Message
from punq import Container

from constants.enums import UserRole
from filters.base_filter import BaseUserFilter


class RootDevOnlyFilter(BaseUserFilter):
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
            tg_id=tg_id,
            current_username=current_username,
            container=container,
        )
        return user is not None and user.role in (UserRole.ROOT, UserRole.DEV)
