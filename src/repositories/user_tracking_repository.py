import logging
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import aliased, selectinload

from database.session import DatabaseContextManager
from models import User
from models.associations import admin_user_tracking

logger = logging.getLogger(__name__)


class UserTrackingRepository:
    def __init__(self, db_manager: DatabaseContextManager) -> None:
        self._db = db_manager

    async def add_user_to_tracking(
        self,
        admin_id: int,
        user_id: int,
    ) -> None:
        """Добавляет пользователя в список отслеживания админа."""
        async with self._db.session() as session:
            admin_result = await session.execute(
                select(User)
                .options(selectinload(User.tracked_users))
                .where(User.id == admin_id)
            )
            admin = admin_result.scalar_one()

            user_result = await session.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one()

            admin.tracked_users.append(user)

            await session.commit()

    async def remove_user_from_tracking(
        self,
        admin_id: int,
        user_id: int,
    ) -> None:
        """Удаляет пользователя из списка отслеживания админа."""
        async with self._db.session() as session:
            admin_result = await session.execute(
                select(User)
                .options(selectinload(User.tracked_users))
                .where(User.id == admin_id)
            )
            admin_user = admin_result.scalar_one()

            tracking_result = await session.execute(
                select(User).where(User.id == user_id)
            )
            tracking_user = tracking_result.scalar_one()

            admin_user.tracked_users.remove(tracking_user)

            await session.commit()

    async def get_tracked_users_by_admin(self, admin_tgid: str) -> list[User]:
        """Получает список отслеживаемых пользователей для админа."""
        async with self._db.session() as session:
            result = await session.execute(
                select(User)
                .options(selectinload(User.tracked_users))
                .where(User.tg_id == admin_tgid)
            )
            admin = result.scalar_one_or_none()

            if not admin:
                return []

            return admin.tracked_users

    async def get_tracked_users_with_dates(
        self, admin_tgid: str
    ) -> list[tuple[User, datetime]]:
        """
        Получает список отслеживаемых пользователей вместе с датой добавления.

        Args:
            admin_tgid: Telegram ID администратора

        Returns:
            Список кортежей (User, created_at)
        """
        async with self._db.session() as session:
            admin_alias = aliased(User)
            stmt = (
                select(User, admin_user_tracking.c.created_at)
                .join(
                    admin_user_tracking,
                    User.id == admin_user_tracking.c.tracked_user_id,
                )
                .join(
                    admin_alias,
                    admin_alias.id == admin_user_tracking.c.admin_id,
                )
                .where(admin_alias.tg_id == admin_tgid)
            )
            result = await session.execute(stmt)
            return [(row[0], row[1]) for row in result.all()]

    async def has_tracked_users(self, admin_tgid: str) -> bool:
        """Проверяет, есть ли у админа отслеживаемые пользователи."""
        async with self._db.session() as session:
            result = await session.execute(
                select(admin_user_tracking.c.tracked_user_id)
                .join(User, User.id == admin_user_tracking.c.admin_id)
                .where(User.tg_id == admin_tgid)
                .limit(1)
            )
            return result.first() is not None

    async def delete_all_tracked_users_for_admin(self, admin_id: int) -> int:
        """Удаляет всех отслеживаемых пользователей для админа."""
        async with self._db.session() as session:
            try:
                query = delete(admin_user_tracking).where(
                    admin_user_tracking.c.admin_id == admin_id
                )
                result = await session.execute(query)
                await session.commit()
                logger.info(
                    "Удалено %d отслеживаемых пользователей для администратора: admin_id=%s",
                    result.rowcount,
                    admin_id,
                )
                return result.rowcount
            except Exception as e:
                logger.error(
                    "Произошла ошибка при удалении всех отслеживаемых пользователей: %s",
                    e,
                )
                await session.rollback()
                raise e
