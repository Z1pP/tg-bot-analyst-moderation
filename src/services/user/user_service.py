import logging
from typing import Optional

from sqlalchemy.exc import IntegrityError

from constants.enums import UserRole
from models import User
from repositories import UserRepository
from services.caching import ICache

logger = logging.getLogger(__name__)


class UserService:
    """
    Сервис для работы с пользователями системы.

    Обеспечивает:
    - Поиск пользователей по ID, Telegram ID и username
    - Автоматическое кеширование в Redis
    - Создание новых пользователей
    - Синхронизацию username при изменениях
    """

    def __init__(self, user_repository: UserRepository, cache: ICache):
        self._user_repository = user_repository
        self._cache = cache

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Получает пользователя по его username с проверкой кеша.

        Args:
            username: Telegram username пользователя

        Returns:
            Объект User или None
        """
        # Проверяем кеш
        user = await self._cache.get(f"user:username:{username}")
        if user:
            return user

        # Ищем в БД
        user = await self._user_repository.get_user_by_username(username=username)
        if user:
            await self._cache_user(user)
        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Получает пользователя по его внутреннему ID в БД.

        Args:
            user_id: ID записи в БД

        Returns:
            Объект User или None
        """
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
        """
        Получает пользователя по Telegram ID или username с проверкой кеша.

        Args:
            tg_id: Telegram ID пользователя
            username: Telegram username пользователя

        Returns:
            Объект User или None
        """
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
        user = None
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
        self,
        tg_id: str = None,
        username: str = None,
        role: Optional[UserRole] = UserRole.USER,
        language: str = "ru",
    ) -> User:
        """
        Создает нового пользователя в системе.

        Args:
            tg_id: Telegram ID
            username: Username
            role: Роль пользователя
            language: Код языка (по умолчанию 'ru')

        Returns:
            Созданный объект User
        """
        user = await self._user_repository.create_user(
            tg_id=tg_id, username=username, role=role, language=language
        )

        if user:
            await self._cache_user(user)
        return user

    async def get_or_create(
        self,
        tg_id: str,
        username: Optional[str] = None,
        role: Optional[UserRole] = UserRole.USER,
        language: str = "ru",
    ) -> User:
        """
        Получает существующего пользователя или создает нового.

        Args:
            tg_id: Telegram ID
            username: Username
            role: Роль пользователя
            language: Код языка

        Returns:
            Объект User
        """
        user = await self.get_user(tg_id=tg_id, username=username)

        if not user:
            try:
                new_user = await self.create_user(
                    username=username, tg_id=tg_id, role=role, language=language
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
        """
        Получает список администраторов для указанного чата.
        Сначала проверяет кеш, затем БД.

        Args:
            chat_tg_id: Telegram ID чата

        Returns:
            Список объектов User
        """
        cache_key = f"chat_admins:{chat_tg_id}"
        admins = await self._cache.get(cache_key)
        if admins is not None:
            return admins

        admins = await self._user_repository.get_admins_for_chat(
            chat_tg_id=chat_tg_id,
        )
        if admins is not None:
            await self._cache.set(cache_key, admins, ttl=300)  # Кешируем на 5 минут
        return admins

    async def update_user_role(self, user_id: int, new_role: str) -> Optional[User]:
        """
        Обновляет роль пользователя и синхронизирует кеш.
        """
        user = await self._user_repository.update_user_role(
            user_id=user_id, new_role=new_role
        )
        if user:
            await self._cache_user(user)
        return user

    async def update_user_language(self, user_id: int, language: str) -> Optional[User]:
        """
        Обновляет язык пользователя и синхронизирует кеш.
        """
        user = await self._user_repository.update_user_language(
            user_id=user_id, language=language
        )
        if user:
            await self._cache_user(user)
        return user

    async def delete_user(self, user_id: int) -> bool:
        """
        Удаляет пользователя и инвалидирует кеш.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        result = await self._user_repository.delete_user(user_id=user_id)
        if result:
            await self._cache.delete(f"user:id:{user_id}")
            if user.tg_id:
                await self._cache.delete(f"user:tg_id:{user.tg_id}")
            if user.username:
                await self._cache.delete(f"user:username:{user.username}")
        return result
