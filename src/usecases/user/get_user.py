from typing import Optional

from models import User
from repositories import UserRepository


class GetUserByTgIdUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, tg_id: str) -> Optional[User]:
        return await self.user_repository.get_user_by_tg_id(tg_id=tg_id)


class GetUserByIdUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: int) -> Optional[User]:
        return await self.user_repository.get_user_by_id(user_id)
