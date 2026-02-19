from typing import Optional

from models import User
from services import UserService


class CreateNewUserUserCase:
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

    async def execute(
        self,
        tg_id: Optional[str] = None,
        username: Optional[str] = None,
    ) -> User:
        return await self._user_service.create_user(
            tg_id=tg_id or "", username=username or ""
        )
