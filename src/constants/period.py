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
    ONE_DAY = "📅 За день"
    ONE_WEEK = "📅 За неделю"
    ONE_MONTH = "📅 За месяц"
    ALL = "📅 За все время"
    CUSTOM = "🔧 За период"

    @classmethod
    def get_all_periods(cls) -> list[str]:
        return [p.value for p in cls if p.value != cls.CUSTOM]

    @classmethod
    def get_all(cls) -> list[str]:
        return [p.value for p in cls]

    def to_datetime(self) -> Tuple[datetime, datetime]:
        now = TimeZoneService.now()

        if self == TimePeriod.THREE_HOURS.value:
            return now - timedelta(hours=3), now
        elif self == TimePeriod.SIX_HOURS.value:
            return now - timedelta(hours=6), now
        elif self == TimePeriod.ONE_DAY.value:
            return now - timedelta(days=1), now
        elif self == TimePeriod.ONE_WEEK.value:
            return now - timedelta(weeks=1), now
        elif self == TimePeriod.ONE_MONTH.value:
            return now - timedelta(days=30), now
        elif self == TimePeriod.ALL.value:
            return now - timedelta(1970, 1, 1), now
        else:
            raise ValueError(f"Неизвестный период: {self}")
