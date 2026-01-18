from dataclasses import dataclass
from typing import Optional

from constants.enums import UserRole
from models import User
from services import UserService


@dataclass
class UserResult:
    user: User
    is_existed: bool


class GetOrCreateUserIfNotExistUserCase:
    def __init__(
        self,
        user_service: UserService,
    ):
        self._user_service = user_service

    async def execute(
        self,
        tg_id: Optional[str] = None,
        username: Optional[str] = None,
        role: Optional[UserRole] = None,
    ) -> UserResult:
        """
        Получает существующего пользователя или создает нового.

        Args:
            tg_id: Telegram ID пользователя
            username: Username пользователя
            role: Role пользователя

        Returns:
            GetOrCreateUserResult с пользователем и флагом создания

        Raises:
            ValueError: Если не предоставлен ни tg_id, ни username
        """
        if not tg_id and not username:
            raise ValueError("Either tg_id or username must be provided")

        user = await self._user_service.get_user(tg_id=tg_id, username=username)

        if user:
            return UserResult(user=user, is_existed=True)

        new_user = await self._user_service.create_user(
            tg_id=tg_id, username=username, role=role
        )
        return UserResult(
            user=new_user,
            is_existed=False,
        )
