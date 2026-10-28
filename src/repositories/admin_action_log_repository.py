import logging
from typing import List, Optional, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from constants.enums import AdminActionType
from models import AdminActionLog, User
from repositories.base import BaseRepository, transactional

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

    @transactional
    async def create_log(
        self,
        session: AsyncSession,
        /,
        admin_id: int,
        action_type: AdminActionType,
        details: Optional[str] = None,
    ) -> AdminActionLog:
        """Создает запись о действии администратора."""
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

    @transactional
    async def get_logs_paginated(
        self, session: AsyncSession, /, page: int = 1, limit: int = 10
    ) -> Tuple[List[AdminActionLog], int]:
        """Получает логи с пагинацией."""
        return await self._get_logs_page_with_total(session, page, limit)

    @transactional
    async def get_logs_by_admin(
        self, session: AsyncSession, /, admin_id: int, page: int = 1, limit: int = 10
    ) -> Tuple[List[AdminActionLog], int]:
        """Получает логи конкретного администратора с пагинацией."""
        return await self._get_logs_page_with_total(
            session, page, limit, AdminActionLog.admin_id == admin_id
        )

    @transactional
    async def get_admins_with_logs(self, session: AsyncSession, /) -> List[Tuple[int, str, str]]:
        """
        Получает список администраторов, у которых есть логи.
        Возвращает список кортежей (admin_id, username, tg_id).
        """
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
