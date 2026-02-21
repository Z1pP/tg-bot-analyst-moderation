import logging
from typing import List, Optional, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from constants.enums import AdminActionType
from exceptions import DatabaseException
from models import AdminActionLog, User
from repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class AdminActionLogRepository(BaseRepository):
    async def _get_logs_page_with_total(
        self,
        session: AsyncSession,
        page: int,
        limit: int,
        where_clause: Optional[ColumnElement[bool]] = None,
    ) -> Tuple[List[AdminActionLog], int]:
        """Возвращает страницу логов и общее количество. Для внутреннего использования."""
        count_stmt = select(func.count(AdminActionLog.id))
        if where_clause is not None:
            count_stmt = count_stmt.where(where_clause)
        total_count = await session.scalar(count_stmt) or 0

        offset = (page - 1) * limit
        stmt = (
            select(AdminActionLog)
            .options(selectinload(AdminActionLog.admin))
            .order_by(desc(AdminActionLog.created_at))
            .offset(offset)
            .limit(limit)
        )
        if where_clause is not None:
            stmt = stmt.where(where_clause)
        result = await session.execute(stmt)
        logs = list(result.scalars().all())
        return logs, total_count

    async def create_log(
        self,
        admin_id: int,
        action_type: AdminActionType,
        details: Optional[str] = None,
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
            except SQLAlchemyError as e:
                logger.error("Ошибка при создании лога действия: %s", e, exc_info=True)
                await session.rollback()
                raise DatabaseException(
                    details={"context": "create_log", "original": str(e)}
                ) from e

    async def get_logs_paginated(
        self, page: int = 1, limit: int = 10
    ) -> Tuple[List[AdminActionLog], int]:
        """Получает логи с пагинацией."""
        async with self._db.session() as session:
            try:
                return await self._get_logs_page_with_total(session, page, limit)
            except SQLAlchemyError as e:
                logger.error("Ошибка при получении логов: %s", e, exc_info=True)
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_logs_paginated", "original": str(e)}
                ) from e

    async def get_logs_by_admin(
        self, admin_id: int, page: int = 1, limit: int = 10
    ) -> Tuple[List[AdminActionLog], int]:
        """Получает логи конкретного администратора с пагинацией."""
        async with self._db.session() as session:
            try:
                return await self._get_logs_page_with_total(
                    session, page, limit, AdminActionLog.admin_id == admin_id
                )
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при получении логов админа %d: %s",
                    admin_id,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_logs_by_admin", "original": str(e)}
                ) from e

    async def get_admins_with_logs(self) -> List[Tuple[int, str, str]]:
        """
        Получает список администраторов, у которых есть логи.
        Возвращает список кортежей (admin_id, username, tg_id).
        """
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
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при получении списка администраторов с логами: %s",
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_admins_with_logs", "original": str(e)}
                ) from e
