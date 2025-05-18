from typing import Optional

from models import User
from repositories import UserRepository


class GetUserFromDatabaseUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, username: str) -> Optional[User]:
        return await self.user_repository.get_user_by_username(username)
