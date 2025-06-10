from datetime import datetime, timedelta
from enum import Enum
from typing import Tuple

from services.time_service import TimeZoneService


class TimePeriod(Enum):
    """
    Перечисления для указания выбора периода создания отчета 📅 🔧
    """

    THREE_HOURS = "📅 За 3 часа"
    SIX_HOURS = "📅 За 6 часов"
    TODAY = "📅 За сегодня"
    YESTERDAY = "📅 За вчера"
    ONE_WEEK = "📅 За неделю"
    ONE_MONTH = "📅 За месяц"
    THREE_MONTH = "📅 За 3 месяца"
    CUSTOM = "🔧 За период"

    @classmethod
    def get_all_periods(cls) -> list[str]:
        return [p.value for p in cls if p.value != cls.CUSTOM]

    @classmethod
    def get_all(cls) -> list[str]:
        return [p.value for p in cls]

    def to_datetime(cls, period: str) -> Tuple[datetime, datetime]:
        now = TimeZoneService.now()

        if period == cls.THREE_HOURS.value:
            return now - timedelta(hours=3), now
        elif period == cls.SIX_HOURS.value:
            return now - timedelta(hours=6), now
        elif period == cls.TODAY.value:
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return start_of_day, now
        elif period == cls.YESTERDAY.value:
            # Начало вчерашнего дня (00:00) до конца вчерашнего дня (23:59:59)
            yesterday = now - timedelta(days=1)
            start_of_yesterday = yesterday.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_of_yesterday = yesterday.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            return start_of_yesterday, end_of_yesterday
        elif period == cls.ONE_WEEK.value:
            return now - timedelta(weeks=1), now
        elif period == cls.ONE_MONTH.value:
            return now - timedelta(days=30), now
        elif period == cls.THREE_MONTH.value:
            return now - timedelta(days=90), now
        else:
            raise ValueError(f"Неизвестный период: {period}")
