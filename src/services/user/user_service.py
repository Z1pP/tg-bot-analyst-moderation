from models import User
from repositories import UserRepository
from services.caching import ICache


class UserService:
    def __init__(self, user_repository: UserRepository, cache: ICache):
        self._user_repository = user_repository
        self._cache = cache

    async def get_user(self, username: str) -> User:
        user = self._cache.get(username)
        if user:
            return user

        user = await self._user_repository.get_user_by_username(username)
        if user:
            self._cache.set(username, user)

        return user

    async def create_user(self, tg_id: str = None, username: str = None) -> User:
        user = await self._user_repository.create_user(tg_id=tg_id, username=username)

        if user:
            self._cache.set(username, user)
        return user
