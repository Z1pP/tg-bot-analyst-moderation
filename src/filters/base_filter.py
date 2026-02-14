from typing import Optional

from aiogram.filters import Filter
from punq import Container

from models.user import User


class BaseUserFilter(Filter):
    """Базовый фильтр для работы с пользователями"""

    async def get_user(
        self,
        tg_id: str,
        current_username: str,
        container: Container,
    ) -> Optional[User]:
        """Получает пользователя из кеша или БД через UserService"""
        from services.user.user_service import UserService

        user_service: UserService = container.resolve(UserService)
        return await user_service.get_user(tg_id=tg_id, username=current_username)
