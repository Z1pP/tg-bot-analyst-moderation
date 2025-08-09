import logging
from typing import List, Optional

from sqlalchemy import delete, select

from constants.enums import UserRole
from database.session import async_session
from models import User

logger = logging.getLogger(__name__)


class UserRepository:
    async def get_user_by_tg_id(self, tg_id: str) -> Optional[User]:
        """Получает пользователя по Telegram ID."""
        async with async_session() as session:
            try:
                result = await session.execute(select(User).where(User.tg_id == tg_id))
                user = result.scalars().first()

                if user:
                    logger.info(
                        "Получен пользователь по tg_id=%s: username=%s, role=%s",
                        tg_id,
                        user.username,
                        user.role,
                    )
                else:
                    logger.info("Пользователь с tg_id=%s не найден", tg_id)

                return user
            except Exception as e:
                logger.error(
                    "Ошибка при получении пользователя по tg_id=%s: %s", tg_id, e
                )
                return None

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получает пользователя по ID."""
        async with async_session() as session:
            try:
                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalars().first()

                if user:
                    logger.info(
                        "Получен пользователь по id=%d: username=%s, role=%s",
                        user_id,
                        user.username,
                        user.role,
                    )
                else:
                    logger.info("Пользователь с id=%d не найден", user_id)

                return user
            except Exception as e:
                logger.error(
                    "Ошибка при получении пользователя по id=%d: %s", user_id, e
                )
                return None

    async def get_all_moderators(self) -> List[User]:
        """Получает список всех модераторов."""
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(User)
                    .where(
                        User.role == UserRole.MODERATOR,
                    )
                    .order_by(User.username),
                )

                users = result.scalars().all()
                logger.info("Получено %d модераторов", len(users))
                return users
            except Exception as e:
                logger.error("Ошибка при получении списка модераторов: %s", e)
                return []

    async def get_all_admins(self) -> List[User]:
        """Получаем всех администраторов из БД"""
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(User)
                    .where(
                        User.role == UserRole.ADMIN,
                    )
                    .order_by(User.username),
                )

                users = result.scalars().all()
                logger.info("Получено %d администраторов", len(users))
                return users
            except Exception as e:
                logger.error("Ошибка при получении списка администраторов: %s", e)
                return []

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Получает пользователя по имени пользователя."""
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(User).where(User.username == username)
                )
                user = result.scalars().first()

                if user:
                    logger.info(
                        "Получен пользователь по username=%s: id=%s, role=%s",
                        username,
                        user.id,
                        user.role,
                    )
                else:
                    logger.info("Пользователь с username=%s не найден", username)

                return user
            except Exception as e:
                logger.error(
                    "Ошибка при получении пользователя по username=%s: %s", username, e
                )
                return None

    async def create_user(
        self,
        tg_id: str = None,
        username: str = None,
        role: Optional[UserRole] = UserRole.USER,
    ) -> User:
        """Создает нового пользователя."""
        if tg_id is None and username is None:
            raise ValueError("tg_id или username должны быть указаны")

        async with async_session() as session:
            try:
                user = User(
                    tg_id=tg_id,
                    username=username,
                    role=role,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

                logger.info(
                    "Создан новый пользователь: id=%s, username=%s, role=%s",
                    user.id,
                    user.username,
                    user.role,
                )
                return user
            except Exception as e:
                logger.error(
                    "Ошибка при создании пользователя (username=%s): %s", username, e
                )
                await session.rollback()
                raise e

    async def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя по его ID"""
        async with async_session() as session:
            try:
                query = delete(User).where(User.id == user_id)
                result = await session.execute(query)
                await session.commit()

                deleted_count = result.rowcount
                if deleted_count > 0:
                    logger.info(f"Удален пользователь с ID={user_id}")
                    return True
                else:
                    logger.warning(
                        f"Пользователь с ID={user_id} не найден для удаления"
                    )
                    return False
            except Exception as e:
                logger.error(f"Ошибка при удалении пользователя с ID={user_id}:{e}")
                await session.rollback()
                raise e
