import logging
from datetime import time
from typing import Optional

from sqlalchemy.exc import IntegrityError

from config import settings
from models import ReportSchedule
from repositories import ReportScheduleRepository

logger = logging.getLogger(__name__)


class ReportScheduleService:
    """Сервис для управления расписанием отправки ежедневных отчетов."""

    def __init__(self, schedule_repository: ReportScheduleRepository) -> None:
        self._schedule_repository = schedule_repository

    async def get_schedule(self, chat_id: int) -> Optional[ReportSchedule]:
        """
        Получает расписание для чата.

        Args:
            chat_id: ID чата

        Returns:
            ReportSchedule или None если не найдено
        """
        return await self._schedule_repository.get_schedule(chat_id=chat_id)

    async def get_or_create_schedule(
        self,
        chat_id: int,
        sent_time: time,
        tz_name: str = None,
        enabled: bool = True,
    ) -> ReportSchedule:
        """
        Получает существующее расписание или создает новое.

        Args:
            chat_id: ID чата
            sent_time: Время отправки отчета
            tz_name: Временная зона (по умолчанию из настроек)
            enabled: Включено ли расписание

        Returns:
            ReportSchedule

        Raises:
            Exception: При ошибках создания/получения
        """
        if tz_name is None:
            tz_name = settings.TIMEZONE

        schedule = await self.get_schedule(chat_id=chat_id)

        if schedule:
            return schedule

        try:
            return await self._schedule_repository.create_schedule(
                chat_id=chat_id,
                tz_name=tz_name,
                sent_time=sent_time,
                enabled=enabled,
            )
        except IntegrityError as e:
            # Race condition: расписание создано параллельно
            if "unique" in str(e).lower() or "chat_id" in str(e).lower():
                logger.warning(
                    "Race condition: расписание для chat_id=%s создано параллельно",
                    chat_id,
                )
                schedule = await self.get_schedule(chat_id=chat_id)
                if schedule:
                    return schedule
            raise

    async def update_sending_time(
        self, chat_id: int, new_time: time
    ) -> Optional[ReportSchedule]:
        """
        Обновляет время отправки отчета.

        Args:
            chat_id: ID чата
            new_time: Новое время отправки

        Returns:
            Обновленное ReportSchedule или None если не найдено
        """
        schedule = await self.get_schedule(chat_id=chat_id)

        if not schedule:
            logger.warning(
                "Попытка обновить несуществующее расписание: chat_id=%s",
                chat_id,
            )
            return None

        return await self._schedule_repository.update_schedule(
            schedule_id=schedule.id, sent_time=new_time
        )

    async def toggle_schedule(
        self, chat_id: int, enabled: bool
    ) -> Optional[ReportSchedule]:
        """
        Включает или отключает рассылку отчетов.

        Args:
            chat_id: ID чата
            enabled: True для включения, False для отключения

        Returns:
            Обновленное ReportSchedule или None если не найдено
        """
        schedule = await self.get_schedule(chat_id=chat_id)

        if not schedule:
            logger.warning(
                "Попытка изменить несуществующее расписание: chat_id=%s",
                chat_id,
            )
            return None

        return await self._schedule_repository.update_schedule(
            schedule_id=schedule.id, enabled=enabled
        )
