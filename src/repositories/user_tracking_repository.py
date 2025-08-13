import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from database.session import async_session
from models import User

logger = logging.getLogger(__name__)


class UserTrackingRepository:
    async def add_user_to_tracking(
        self,
        admin_username: str,
        user_username: str,
    ) -> bool:
        """Добавляет пользователя в список отслеживания админа."""
        async with async_session() as session:
            try:
                # Используем first() вместо scalar_one_or_none() для обработки дубликатов
                admin_result = await session.execute(
                    select(User)
                    .options(selectinload(User.tracked_users))
                    .where(User.username == admin_username)
                )
                admin_user = admin_result.first()
                admin_user = admin_user[0] if admin_user else None

                if not admin_user:
                    logger.warning(f"Админ c username={admin_username} не найден")
                    return False

                tracking_result = await session.execute(
                    select(User).where(User.username == user_username)
                )
                tracking_user = tracking_result.first()
                tracking_user = tracking_user[0] if tracking_user else None

                if not tracking_user:
                    logger.warning(f"Пользователь c username={user_username} не найден")
                    return False

                # Проверяем существующую связь
                if tracking_user in admin_user.tracked_users:
                    logger.info(
                        f"Пользователь {user_username} уже отслеживается админом {admin_username}"
                    )
                    return True

                admin_user.tracked_users.append(tracking_user)
                await session.commit()

                logger.info(
                    f"Пользователь {user_username} добавлен в отслеживание админом {admin_username}"
                )
                return True

            except SQLAlchemyError as e:
                logger.error(f"Ошибка добавления в отслеживание: {e}")
                await session.rollback()
                return False

    async def remove_user_from_tracking(
        self,
        admin_username: str,
        user_username: str,
    ) -> bool:
        """Удаляет пользователя из списка отслеживания админа."""
        async with async_session() as session:
            try:
                admin_result = await session.execute(
                    select(User)
                    .options(selectinload(User.tracked_users))
                    .where(User.username == admin_username)
                )
                admin_user = admin_result.first()
                admin_user = admin_user[0] if admin_user else None

                if not admin_user:
                    logger.warning(f"Админ не найден: admin_username={admin_username}")
                    return False

                tracking_result = await session.execute(
                    select(User).where(User.username == user_username)
                )
                tracking_user = tracking_result.first()
                tracking_user = tracking_user[0] if tracking_user else None

                if not tracking_user:
                    logger.warning(
                        f"Пользователь не найден: user_username={user_username}"
                    )
                    return False

                if tracking_user in admin_user.tracked_users:
                    admin_user.tracked_users.remove(tracking_user)
                    await session.commit()
                    logger.info(
                        f"Пользователь {user_username} удален из отслеживания админом {admin_username}"
                    )
                    return True

                logger.info(
                    f"Пользователь {user_username} не отслеживался админом {admin_username}"
                )
                return True

            except SQLAlchemyError as e:
                logger.error(f"Ошибка удаления из отслеживания: {e}")
                await session.rollback()
                return False


async def get_tracked_users_by_admin(self, admin_username: str) -> list[User]:
    """Получает список отслеживаемых пользователей для админа."""
    async with async_session() as session:
        try:
            result = await session.execute(
                select(User)
                .options(selectinload(User.tracked_users))
                .where(User.username == admin_username)
            )
            admin_user = result.first()
            admin_user = admin_user[0] if admin_user else None

            if not admin_user:
                logger.warning(f"Админ не найден: admin_username={admin_username}")
                return []

            return list(admin_user.tracked_users)

        except SQLAlchemyError as e:
            logger.error(f"Ошибка получения отслеживаемых пользователей: {e}")
            return []

    async def is_user_tracked_by_admin(
        self, admin_username: str, user_username: str
    ) -> bool:
        """Проверяет, отслеживается ли пользователь админом."""
        tracked_users = await self.get_tracked_users_by_admin(admin_username)
        return any(user.username == user_username for user in tracked_users)
