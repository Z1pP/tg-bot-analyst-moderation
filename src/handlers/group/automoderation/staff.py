"""Проверка прав staff для колбэков карточки авто-модерации (без фильтра Message-only)."""

from aiogram.types import CallbackQuery
from punq import Container

from constants.enums import UserRole
from services.user.user_service import UserService


async def is_automoderation_staff(
    callback: CallbackQuery, container: Container
) -> bool:
    """True, если пользователь — staff по роли в БД."""
    u = callback.from_user
    user_service: UserService = container.resolve(UserService)
    user = await user_service.get_user(
        tg_id=str(u.id),
        username=u.username or "",
    )
    if not user:
        return False
    return user.role in (
        UserRole.ADMIN,
        UserRole.MODERATOR,
        UserRole.DEV,
        UserRole.ROOT,
        UserRole.OWNER,
    )
