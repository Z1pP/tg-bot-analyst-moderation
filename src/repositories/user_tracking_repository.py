import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.session import DatabaseContextManager
from models import User

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
