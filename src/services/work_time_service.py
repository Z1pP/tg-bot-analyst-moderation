from datetime import datetime, time, timedelta
from typing import Optional

from constants.work_time import TOLERANCE, WORK_END, WORK_START
from models import ChatMessage, MessageReply

from .time_service import TimeZoneService


class WorkTimeService:
    """
    Сервис который устанавливает рабочее время для последующей логики
    """

    @classmethod
    def is_work_time(
        cls,
        current_time: time,
        *,
        work_start: Optional[time] = None,
        work_end: Optional[time] = None,
        tolerance: Optional[int] = None,
    ):
        """
        Проверяет, входит ли время в рабочие часы с учетом допустимого отклонения.
        """
        # Вычисляем границы рабочего времени с учетом допуска
        start_with_tolerance = WorkTimeService._adjust_time_with_tolerance(
            base_time=work_start or WORK_START,
            delta=-(tolerance or TOLERANCE),
        )
        end_with_tolerance = WorkTimeService._adjust_time_with_tolerance(
            base_time=work_end or WORK_END,
            delta=tolerance or TOLERANCE,
        )

        # Проверяем, входит ли время в диапазон
        return start_with_tolerance <= current_time <= end_with_tolerance

    @classmethod
    def _adjust_time_with_tolerance(cls, base_time: time, delta: timedelta) -> time:
        """
        Корректирует время с учетом допуска.
        """
        # Преобразуем time в datetime для выполнения арифметических операций
        dt = datetime.combine(TimeZoneService.now(), base_time)
        # Применяем смещение
        adjusted_dt = dt + delta
        # Возвращаем только компонент времени
        return adjusted_dt.time()

    @classmethod
    def filter_by_work_time(
        cls, items: list[MessageReply | ChatMessage]
    ) -> list[MessageReply | ChatMessage]:
        """
        Фильтрует ответы в пределах рабочего времени
        """
        start_work_time = cls._adjust_time_with_tolerance(WORK_START, -TOLERANCE)
        end_work_time = cls._adjust_time_with_tolerance(WORK_END, TOLERANCE)

        return [
            item
            for item in items
            if start_work_time <= item.created_at.time() <= end_work_time
        ]
