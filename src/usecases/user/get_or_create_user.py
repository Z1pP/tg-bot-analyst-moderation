from dataclasses import dataclass
from typing import Optional

from models import User
from repositories.user_repository import UserRepository


@dataclass
class UserResult:
    user: User
    is_existed: bool


class GetOrCreateUserIfNotExistUserCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(
        self,
        tg_id: Optional[str] = None,
        username: Optional[str] = None,
    ) -> UserResult:
        """
        Получает существующего пользователя или создает нового.

        Args:
            tg_id: Telegram ID пользователя
            username: Username пользователя

        Returns:
            GetOrCreateUserResult с пользователем и флагом создания

        Raises:
            ValueError: Если не предоставлен ни tg_id, ни username
        """
        if not tg_id and not username:
            raise ValueError("Either tg_id or username must be provided")

        user = await self._get_user(tg_id, username)

        if user:
            return UserResult(user=user, is_existed=True)

        return UserResult(
            user=await self._create_user(tg_id, username),
            is_existed=False,
        )

    async def _get_user(
        self,
        tg_id: Optional[str],
        username: Optional[str],
    ) -> Optional[User]:
        """
        Получает пользователя по tg_id или username
        """
        if tg_id:
            return await self.user_repository.get_user_by_tg_id(tg_id)
        return await self.user_repository.get_user_by_username(username)

    async def _create_user(
        self,
        tg_id: Optional[str],
        username: Optional[str],
    ) -> User:
        """
        Создает нового пользователя
        """
        return await self.user_repository.create_user(tg_id=tg_id, username=username)
