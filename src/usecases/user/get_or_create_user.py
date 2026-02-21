from dataclasses import dataclass
from typing import Optional

from constants.enums import UserRole
from exceptions import ValidationException
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
            ValidationException: Если не предоставлен ни tg_id, ни username
        """
        if not tg_id and not username:
            raise ValidationException(
                message="Необходимо указать tg_id или username"
            )

        tg_id_str = tg_id or ""
        username_str = username or ""
        user = await self._user_service.get_user(
            tg_id=tg_id_str, username=username_str
        )

        if user:
            return UserResult(user=user, is_existed=True)

        new_user = await self._user_service.create_user(
            tg_id=tg_id_str, username=username_str, role=role
        )
        return UserResult(
            user=new_user,
            is_existed=False,
        )
