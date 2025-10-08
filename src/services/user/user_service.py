import logging

from sqlalchemy.exc import IntegrityError

from models import User
from repositories import UserRepository
from services.caching import ICache

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, user_repository: UserRepository, cache: ICache):
        self._user_repository = user_repository
        self._cache = cache

    async def get_user(self, tg_id: str, username: str = None) -> User:
        user = await self._cache.get(tg_id)
        if user:
            if username and user.username != username:
                user = await self._user_repository.update_user(
                    user_id=user.id,
                    username=username,
                )
                await self._cache.set(tg_id, user)
            return user

        user = await self._user_repository.get_user_by_tg_id(tg_id)
        if user:
            if username and user.username != username:
                user = await self._user_repository.update_user(
                    user_id=user.id,
                    username=username,
                )
            await self._cache.set(tg_id, user)

        return user

    async def create_user(self, tg_id: str = None, username: str = None) -> User:
        user = await self._user_repository.create_user(tg_id=tg_id, username=username)

        if user:
            await self._cache.set(tg_id, user)
        return user

    async def get_or_create(self, username: str, tg_id: str) -> User:
        user = await self.get_user(tg_id=tg_id)

        if not user:
            try:
                new_user = await self.create_user(username=username, tg_id=tg_id)

                await self._cache.set(tg_id, new_user)

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
