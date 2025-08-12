from dataclasses import dataclass
from typing import Optional

from constants.enums import UserRole
from models import User
from repositories.user_repository import UserRepository
from services.caching import ICache


@dataclass
class UserResult:
    user: User
    is_existed: bool


class GetOrCreateUserIfNotExistUserCase:
    def __init__(
        self,
        user_repository: UserRepository,
        cache_service: ICache,
    ):
        self.user_repository = user_repository
        self.cache_service = cache_service

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

        user = await self._get_user(tg_id=tg_id, username=username)

        if user:
            return UserResult(user=user, is_existed=True)

        return UserResult(
            user=await self._create_user(tg_id, username, role),
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
            user = self.cache_service.get(key=tg_id)
            if user:
                return user

            user = user = await self.user_repository.get_user_by_tg_id(tg_id)
            if user:
                self.cache_service.set(key=tg_id, value=user)
                return user
        if username:
            return await self.user_repository.get_user_by_username(username)
        return None

    async def _create_user(
        self,
        tg_id: Optional[str],
        username: Optional[str],
        role: Optional[UserRole] = None,
    ) -> User:
        """
        Создает нового пользователя
        """
        user = await self.user_repository.create_user(
            tg_id=tg_id,
            username=username,
            role=role,
        )
        self.cache_service.set(key=tg_id, value=user)
        return user
