from datetime import datetime, timedelta
from enum import Enum
from typing import Tuple

from services.time_service import TimeZoneService


class TimePeriod(Enum):
    """
    Перечисления для указания выбора периода создания отчета
    """

    TODAY = "За сегодня"
    YESTERDAY = "За вчера"
    ONE_WEEK = "За неделю"
    ONE_MONTH = "За месяц"
    CUSTOM = "За другой период"

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

        if period == cls.TODAY.value:
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

        else:
            raise ValueError(f"Неизвестный период: {period}")


class SummaryTimePeriod(Enum):
    """
    Перечисления для указания выбора периода создания сводки
    """

    LAST_24_HOURS = "За последние 24 часа"

    @classmethod
    def to_datetime(cls, period: str) -> Tuple[datetime, datetime]:
        """
        Преобразует строковое представление периода в пару дат (начало, конец).
        """
        now = TimeZoneService.now()

        if period == cls.LAST_24_HOURS.value:
            # Последние 24 часа от текущего момента
            start_of_24h = now - timedelta(hours=24)
            return start_of_24h, now

        else:
            raise ValueError(f"Неизвестный период сводки: {period}")
