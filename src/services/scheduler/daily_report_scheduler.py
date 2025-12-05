import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from constants.period import TimePeriod
from services.time_service import TimeZoneService
from usecases.report.chat.send_daily_chat_reports import SendDailyChatReportsUseCase

logger = logging.getLogger(__name__)


class DailyReportSchedulerService:
    """Сервис для планирования ежедневной отправки отчетов в архивные чаты."""

    def __init__(self, report_usecase: SendDailyChatReportsUseCase):
        self._report_usecase = report_usecase
        self._scheduler: Optional[AsyncIOScheduler] = None

    def start_scheduler(self) -> None:
        """Запускает планировщик для ежедневной отправки отчетов в 22:10."""
        if self._scheduler is not None:
            logger.warning("Планировщик уже запущен")
            return

        logger.info("Запуск планировщика ежедневных отчетов")

        # Создаем планировщик с временной зоной из TimeZoneService
        self._scheduler = AsyncIOScheduler(timezone=TimeZoneService.DEFAULT_TIMEZONE)

        # Добавляем задачу на 22:10 каждый день
        self._scheduler.add_job(
            func=self._send_reports,
            trigger=CronTrigger(hour=19, minute=10),
            id="daily_chat_reports",
            name="Ежедневная отправка отчетов по чатам",
            replace_existing=True,
        )

        # Запускаем планировщик
        self._scheduler.start()

        logger.info(
            "Планировщик запущен. Отчеты будут отправляться каждый день в 22:10 по времени %s",
            TimeZoneService.DEFAULT_TIMEZONE,
        )

    def stop_scheduler(self) -> None:
        """Останавливает планировщик."""
        if self._scheduler is None:
            logger.warning("Планировщик не запущен")
            return

        logger.info("Остановка планировщика ежедневных отчетов")
        self._scheduler.shutdown(wait=True)
        self._scheduler = None
        logger.info("Планировщик остановлен")

    async def _send_reports(self) -> None:
        """Внутренний метод для отправки отчетов (вызывается планировщиком)."""
        logger.info("Запуск задачи отправки ежедневных отчетов")
        try:
            await self._report_usecase.execute(period=TimePeriod.TODAY.value)
            logger.info("Задача отправки ежедневных отчетов завершена успешно")
        except Exception as e:
            logger.error(
                "Ошибка при выполнении задачи отправки ежедневных отчетов: %s",
                e,
                exc_info=True,
            )
