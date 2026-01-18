from typing import Optional

from models import User
from services import UserService


class GetUserByTgIdUseCase:
    def __init__(self, user_service: UserService):
        self._user_service = user_service

    async def execute(self, tg_id: str) -> Optional[User]:
        return await self._user_service.get_user(tg_id=tg_id)


class GetUserByIdUseCase:
    def __init__(self, user_service: UserService):
        self._user_service = user_service

    async def execute(self, user_id: int) -> Optional[User]:
        return await self._user_service.get_user_by_id(user_id)
