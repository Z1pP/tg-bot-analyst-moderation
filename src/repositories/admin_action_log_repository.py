import logging
from typing import List, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.orm import selectinload

from constants.enums import AdminActionType
from models import AdminActionLog
from repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class AdminActionLogRepository(BaseRepository):
    async def create_log(
        self, admin_id: int, action_type: AdminActionType, details: str = None
    ) -> AdminActionLog:
        """Создает запись о действии администратора."""
        async with self._db.session() as session:
            try:
                log_entry = AdminActionLog(
                    admin_id=admin_id,
                    action_type=action_type.value,  # Явно используем значение enum
                    details=details,
                )
                session.add(log_entry)
                await session.commit()
                await session.refresh(log_entry)
                logger.info(
                    "Создан лог действия: admin_id=%d, action_type=%s, details=%s",
                    admin_id,
                    action_type.value,
                    details,
                )
                return log_entry
            except Exception as e:
                logger.error("Ошибка при создании лога действия: %s", e, exc_info=True)
                await session.rollback()
                raise

    async def get_logs_paginated(
        self, page: int = 1, limit: int = 10
    ) -> Tuple[List[AdminActionLog], int]:
        """Получает логи с пагинацией."""
        async with self._db.session() as session:
            try:
                # Получаем общее количество логов
                count_query = select(func.count(AdminActionLog.id))
                total_count = await session.scalar(count_query)

                # Получаем логи с пагинацией
                offset = (page - 1) * limit
                query = (
                    select(AdminActionLog)
                    .options(selectinload(AdminActionLog.admin))
                    .order_by(desc(AdminActionLog.created_at))
                    .offset(offset)
                    .limit(limit)
                )
                result = await session.execute(query)
                logs = list(result.scalars().all())

                return logs, total_count or 0
            except Exception as e:
                logger.error("Ошибка при получении логов: %s", e, exc_info=True)
                raise

    async def get_logs_by_admin(
        self, admin_id: int, page: int = 1, limit: int = 10
    ) -> Tuple[List[AdminActionLog], int]:
        """Получает логи конкретного администратора с пагинацией."""
        async with self._db.session() as session:
            try:
                # Получаем общее количество логов для админа
                count_query = select(func.count(AdminActionLog.id)).where(
                    AdminActionLog.admin_id == admin_id
                )
                total_count = await session.scalar(count_query)

                # Получаем логи с пагинацией
                offset = (page - 1) * limit
                query = (
                    select(AdminActionLog)
                    .options(selectinload(AdminActionLog.admin))
                    .where(AdminActionLog.admin_id == admin_id)
                    .order_by(desc(AdminActionLog.created_at))
                    .offset(offset)
                    .limit(limit)
                )
                result = await session.execute(query)
                logs = list(result.scalars().all())

                return logs, total_count or 0
            except Exception as e:
                logger.error(
                    "Ошибка при получении логов админа %d: %s",
                    admin_id,
                    e,
                    exc_info=True,
                )
                raise

    async def get_admins_with_logs(self) -> List[Tuple[int, str, str]]:
        """
        Получает список администраторов, у которых есть логи.
        Возвращает список кортежей (admin_id, username, tg_id).
        """
        from models import User

        async with self._db.session() as session:
            try:
                # Получаем уникальных администраторов, у которых есть логи
                query = (
                    select(
                        User.id,
                        User.username,
                        User.tg_id,
                    )
                    .join(AdminActionLog, User.id == AdminActionLog.admin_id)
                    .distinct()
                    .order_by(User.username)
                )
                result = await session.execute(query)
                admins = result.all()
                return [
                    (admin_id, username or f"ID:{tg_id}", tg_id)
                    for admin_id, username, tg_id in admins
                ]
            except Exception as e:
                logger.error(
                    "Ошибка при получении списка администраторов с логами: %s",
                    e,
                    exc_info=True,
                )
                raise
