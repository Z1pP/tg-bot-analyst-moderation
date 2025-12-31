import logging
from typing import Optional

from sqlalchemy.exc import IntegrityError

from models import User
from repositories import UserRepository
from services.caching import ICache

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, user_repository: UserRepository, cache: ICache):
        self._user_repository = user_repository
        self._cache = cache

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self._user_repository.get_user_by_username(username=username)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        # Проверяем кеш
        user = await self._cache.get(f"user:id:{user_id}")
        if user:
            return user

        # Ищем в БД
        user = await self._user_repository.get_user_by_id(user_id=user_id)
        if user:
            await self._cache_user(user)
        return user

    async def get_user(self, tg_id: str = None, username: str = None) -> Optional[User]:
        # Проверяем кеш по tg_id
        if tg_id:
            user = await self._cache.get(f"user:tg_id:{tg_id}")
            if user:
                if username and user.username != username:
                    user = await self._user_repository.update_user(
                        user_id=user.id,
                        username=username,
                    )
                    await self._cache_user(user)
                return user

        # Проверяем кеш по username
        if username:
            user = await self._cache.get(f"user:username:{username}")
            if user:
                return user

        # Ищем в БД
        if tg_id:
            user = await self._user_repository.get_user_by_tg_id(tg_id=tg_id)

        if not user and username:
            user = await self._user_repository.get_user_by_username(username=username)

        if user:
            if username and user.username != username:
                user = await self._user_repository.update_user(
                    user_id=user.id,
                    username=username,
                )
            await self._cache_user(user)

        return user

    async def _cache_user(self, user: User) -> None:
        """Кеширует пользователя по id, tg_id и username"""
        if user.id:
            await self._cache.set(f"user:id:{user.id}", user)
        if user.tg_id:
            await self._cache.set(f"user:tg_id:{user.tg_id}", user)
        if user.username:
            await self._cache.set(f"user:username:{user.username}", user)

    async def create_user(
        self, tg_id: str = None, username: str = None, language: str = "ru"
    ) -> User:
        user = await self._user_repository.create_user(
            tg_id=tg_id, username=username, language=language
        )

        if user:
            await self._cache_user(user)
        return user

    async def get_or_create(
        self, username: str, tg_id: str, language: str = "ru"
    ) -> User:
        user = await self.get_user(tg_id=tg_id, username=username)

        if not user:
            try:
                new_user = await self.create_user(
                    username=username, tg_id=tg_id, language=language
                )
                return new_user
            except IntegrityError as e:
                # Race condition: пользователь создан параллельно
                if "tg_id" in str(e) and "duplicate key" in str(e):
                    logger.warning(
                        f"Race condition: пользователь с tg_id={tg_id} создан параллельно"
                    )
                    # Получаем созданного пользователя
                    user = await self.get_user(tg_id=tg_id)
                    if user:
                        return user
                raise

        return user

    async def get_admins_for_chat(self, chat_tg_id: str) -> list[User]:
        return await self._user_repository.get_admins_for_chat(
            chat_tg_id=chat_tg_id,
        )
