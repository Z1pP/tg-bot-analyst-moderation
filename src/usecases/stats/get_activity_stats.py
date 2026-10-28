"""Use case: статистика активности по дням для Mini App."""

import logging
from datetime import timedelta

from dto.stats import ActivityDayDTO, ActivityStatsDTO
from repositories import MessageRepository, PunishmentRepository
from services.time_service import TimeZoneService

logger = logging.getLogger(__name__)


class GetActivityStatsUseCase:
    """Считает сообщения, варны и баны по дням за выбранный период."""

    def __init__(
        self,
        message_repository: MessageRepository,
        punishment_repository: PunishmentRepository,
    ) -> None:
        self._message_repository = message_repository
        self._punishment_repository = punishment_repository

    async def execute(self, days_count: int) -> ActivityStatsDTO:
        """Возвращает активность по дням, начиная с самого раннего дня."""
        now = TimeZoneService.now()
        period_start = (now - timedelta(days=days_count - 1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        period_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        try:
            daily_punishments = (
                await self._punishment_repository.get_daily_punishment_counts(
                    start=period_start, end=period_end
                )
            )
        except Exception as e:
            logger.warning("Не удалось получить статистику наказаний: %s", e)
            daily_punishments = {}

        day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        result: list[ActivityDayDTO] = []

        for i in range(days_count - 1, -1, -1):
            day = now - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            date_str = day.strftime("%Y-%m-%d")

            try:
                messages = await self._message_repository.count_messages_by_date_range(
                    start=day_start,
                    end=day_end,
                )
            except Exception as e:
                logger.warning(
                    "Не удалось получить сообщения за %s: %s", date_str, e
                )
                messages = 0

            punishments = daily_punishments.get(date_str, {"warns": 0, "bans": 0})
            result.append(
                ActivityDayDTO(
                    day=day_names[day.weekday()],
                    date=date_str,
                    messages=messages,
                    warns=punishments["warns"],
                    bans=punishments["bans"],
                )
            )

        return ActivityStatsDTO(activity=result, days=days_count)