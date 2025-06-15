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

    @classmethod
    def to_datetime(cls, period: str) -> Tuple[datetime, datetime]:
        """
        Преобразует строковое представление периода в пару дат (начало, конец).

        Args:
            period: Строковое представление периода (значение из TimePeriod)

        Returns:
            Кортеж из двух дат: (начало периода, конец периода)
        """
        now = TimeZoneService.now()

        # Текущий день
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if period == cls.THREE_HOURS.value:
            return now - timedelta(hours=3), now

        elif period == cls.SIX_HOURS.value:
            return now - timedelta(hours=6), now

        elif period == cls.TODAY.value:
            return start_of_today, now

        elif period == cls.YESTERDAY.value:
            # Вчерашний день от 00:00 до 23:59:59
            yesterday = now - timedelta(days=1)
            start_of_yesterday = yesterday.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_of_yesterday = yesterday.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            return start_of_yesterday, end_of_yesterday

        elif period == cls.ONE_WEEK.value:
            # Последние 7 дней, включая сегодня
            # Начало недели - 7 дней назад в 00:00
            start_of_week = (now - timedelta(days=6)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            return start_of_week, now

        elif period == cls.ONE_MONTH.value:
            # Последние 30 дней, включая сегодня
            # Начало месяца - 30 дней назад в 00:00
            start_of_month = (now - timedelta(days=29)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            return start_of_month, now

        elif period == cls.THREE_MONTH.value:
            # Последние 90 дней, включая сегодня
            # Начало 3-месячного периода - 90 дней назад в 00:00
            start_of_three_months = (now - timedelta(days=89)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            return start_of_three_months, now

        else:
            raise ValueError(f"Неизвестный период: {period}")
