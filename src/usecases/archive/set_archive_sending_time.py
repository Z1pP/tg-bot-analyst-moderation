"""Use case: установка/обновление времени отправки отчётов в архив."""

from __future__ import annotations

import logging
from datetime import time
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from exceptions import DatabaseException
from services.report_schedule_service import ReportScheduleService

logger = logging.getLogger(__name__)


class SetArchiveSendingTimeResult:
    """Результат установки времени отправки."""

    __slots__ = ("success", "error")

    def __init__(self, success: bool, error: Optional[str] = None) -> None:
        self.success = success
        self.error = error


class SetArchiveSendingTimeUseCase:
    """Устанавливает или обновляет время отправки ежедневного отчёта в архив."""

    def __init__(self, report_schedule_service: ReportScheduleService) -> None:
        self._schedule_service = report_schedule_service

    async def execute(
        self, chat_id: int, new_time: time
    ) -> SetArchiveSendingTimeResult:
        """
        Создаёт расписание или обновляет время отправки.

        Returns:
            SetArchiveSendingTimeResult(success=True) или success=False с error.
        """
        try:
            schedule = await self._schedule_service.get_schedule(chat_id=chat_id)
            if schedule:
                updated = await self._schedule_service.update_sending_time(
                    chat_id=chat_id, new_time=new_time
                )
                if not updated:
                    return SetArchiveSendingTimeResult(
                        success=False, error="update_failed"
                    )
            else:
                await self._schedule_service.get_or_create_schedule(
                    chat_id=chat_id,
                    sent_time=new_time,
                    enabled=True,
                )
            return SetArchiveSendingTimeResult(success=True)
        except SQLAlchemyError as exc:
            logger.error(
                "Ошибка при сохранении времени отправки: %s", exc, exc_info=True
            )
            raise DatabaseException(
                details={"context": "set_archive_sending_time", "original": str(exc)}
            ) from exc
