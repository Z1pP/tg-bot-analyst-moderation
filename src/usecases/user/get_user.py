from typing import Optional

from exceptions import ValidationException
from models import User
from services import UserService


class GetUserByUsernameUseCase:
    """Use case: получение пользователя по username."""

    def __init__(self, user_service: UserService):
        self._user_service = user_service

    async def execute(self, username: str) -> Optional[User]:
        return await self._user_service.get_by_username(username=username)


class GetUserByTgIdUseCase:
    def __init__(self, user_service: UserService):
        self._user_service = user_service

    async def execute(self, tg_id: str) -> Optional[User]:
        if not tg_id or not str(tg_id).strip():
            raise ValidationException(message="❌ Не указан идентификатор пользователя.")
        return await self._user_service.get_user(tg_id=str(tg_id).strip())


class GetUserByIdUseCase:
    def __init__(self, user_service: UserService):
        self._user_service = user_service

    async def execute(self, user_id: int) -> Optional[User]:
        return await self._user_service.get_user_by_id(user_id=user_id)
