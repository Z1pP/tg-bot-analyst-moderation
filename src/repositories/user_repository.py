import logging
from typing import List, Optional

from sqlalchemy import delete, select

from constants.enums import UserRole
from database.session import async_session
from models import User

logger = logging.getLogger(__name__)


class UserRepository:

    async def update_tg_id(self, user_id: int, new_tg_id: str) -> User:
        """Обновляет tg_id пользователя."""
        async with async_session() as session:
            try:
                user = await session.get(User, user_id)
                if user:
                    user.tg_id = new_tg_id
                    await session.commit()
                    logger.info(
                        "Пользователь %s обновлен: tg_id=%s",
                        user_id,
                        new_tg_id,
                    )
                else:
                    logger.info("Пользователь %s не найден", user_id)
                return user
            except Exception as e:
                logger.error(
                    "Ошибка при обновлении tg_id пользователя %s: %s",
                    user_id,
                    e,
                )
                return None

    async def update_username(self, user_id: int, new_username: str) -> Optional[User]:
        """Обновляет username пользователя только при изменении."""
        async with async_session() as session:
            try:
                user = await session.get(User, user_id)
                if not user:
                    logger.warning(f"Пользователь {user_id} не найден")
                    return None

                # Проверяем нужно ли обновление
                if user.username == new_username:
                    return user  # Нет изменений

                user.username = new_username
                await session.commit()
                logger.info(
                    f"Username обновлен для пользователя {user_id}: {new_username}"
                )
                return user
            except Exception as e:
                logger.error(
                    f"Ошибка при обновлении username пользователя {user_id}: {e}"
                )
                await session.rollback()
                raise

    async def get_user_by_tg_id(self, tg_id: str) -> Optional[User]:
        """Получает пользователя по Telegram ID."""
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(User).where(User.tg_id == tg_id),
                )
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

    async def get_tracked_users_for_admin(self, admin_tg_id: str) -> List[User]:
        async with async_session() as session:
            try:
                query = (
                    select(User)
                    .join(User.tracked_users)
                    .where(User.tg_id == admin_tg_id)
                    .order_by(User.username)
                )
                result = await session.execute(query)

                tracked_users = result.scalars().all()
                logger.info(
                    f"Получено {len(tracked_users)} отслеживаемых "
                    f"пользователей для администратора TG_ID:{admin_tg_id}"
                )
                return tracked_users
            except Exception as e:
                logger.error(
                    "Ошибка при получении отслеживаемых пользователей "
                    f"для администратора с TG_ID:{admin_tg_id}: {e}"
                )
                raise

    async def get_tracked_user(self, admin_tg_id: str, user_tg_id) -> Optional[User]:
        async with async_session() as session:
            try:
                query = (
                    select(User)
                    .join(User.tracked_users)
                    .where(User.tg_id == admin_tg_id)
                    .where(User.tracked_users.any(tg_id=user_tg_id))
                )
                result = await session.execute(query)

                tracked_user = result.scalars().first()
                logger.info(
                    f"Получен отслеживаемый пользователь с TG_ID:{user_tg_id} "
                    f"для администратора TG_ID:{admin_tg_id}"
                )
                return tracked_user
            except Exception as e:
                logger.error(
                    "Ошибка при получении отслеживаемого пользователя "
                    f"с TG_ID:{user_tg_id} для администратора TG_ID:{admin_tg_id}: {e}"
                )
                raise

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
