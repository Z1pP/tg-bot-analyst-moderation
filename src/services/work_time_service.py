from datetime import datetime, time, timedelta
from typing import Optional, Tuple

from constants.work_time import TOLERANCE, WORK_END, WORK_START
from models import ChatMessage, MessageReply

from .time_service import TimeZoneService


class WorkTimeService:
    """
    Сервис для работы с рабочим временем.

    Предоставляет методы для проверки, фильтрации и корректировки времени
    в соответствии с установленными рабочими часами и допустимыми отклонениями.

    Рабочее время определяется константами WORK_START и WORK_END,
    а допустимое отклонение - константой TOLERANCE.
    """

    @classmethod
    def is_work_time(
        cls,
        current_time: time,
        *,
        work_start: Optional[time] = None,
        work_end: Optional[time] = None,
        tolerance: Optional[int] = None,
    ) -> bool:
        """
        Проверяет, входит ли время в рабочие часы с учетом допустимого отклонения.

        Args:
            current_time: Время для проверки
            work_start: Начало рабочего времени (по умолчанию WORK_START)
            work_end: Конец рабочего времени (по умолчанию WORK_END)
            tolerance: Допустимое отклонение в минутах (по умолчанию TOLERANCE)

        Returns:
            True, если время входит в рабочие часы с учетом допуска, иначе False
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
    def _adjust_time_with_tolerance(
        cls,
        base_time: time,
        delta: timedelta | int,
    ) -> time:
        """
        Корректирует время с учетом допуска.

        Преобразует объект time в datetime, добавляет или вычитает
        указанное количество минут, и возвращает результат как time.

        Args:
            base_time: Исходное время
            delta: Смещение в минутах (положительное или отрицательное)

        Returns:
            Скорректированное время
        """
        # Преобразуем time в datetime для выполнения арифметических операций
        dt = datetime.combine(TimeZoneService.now().date(), base_time)

        # Проверяем тип delta и применяем смещение
        if isinstance(delta, timedelta):
            adjusted_dt = dt + delta
        else:
            adjusted_dt = dt + timedelta(minutes=delta)

        # Возвращаем только компонент времени
        return adjusted_dt.time()

    @classmethod
    def filter_by_work_time(
        cls, items: list[MessageReply | ChatMessage]
    ) -> list[MessageReply | ChatMessage]:
        """
        Фильтрует элементы, оставляя только те, которые созданы в рабочее время.

        Использует время создания (created_at) каждого элемента для проверки,
        входит ли оно в рабочие часы с учетом допустимого отклонения.

        Args:
            items: Список сообщений или ответов для фильтрации

        Returns:
            Отфильтрованный список элементов, созданных в рабочее время
        """
        start_work_time = cls._adjust_time_with_tolerance(WORK_START, -TOLERANCE)
        end_work_time = cls._adjust_time_with_tolerance(WORK_END, TOLERANCE)

        return [
            item
            for item in items
            if start_work_time <= item.created_at.time() <= end_work_time
        ]

    @classmethod
    def adjust_dates_to_work_hours(
        cls,
        start_date: datetime,
        end_date: datetime,
    ) -> Tuple[datetime, datetime]:
        """
        Корректирует даты начала и конца в соответствии с рабочими часами.

        Если время начала раньше рабочего времени (с учетом допуска),
        устанавливает его на начало рабочего времени.
        Если время окончания позже рабочего времени (с учетом допуска),
        устанавливает его на конец рабочего времени.

        Args:
            start_date: Дата и время начала
            end_date: Дата и время окончания

        Returns:
            Кортеж из скорректированных дат начала и окончания
        """
        start_work_time = cls._adjust_time_with_tolerance(WORK_START, -TOLERANCE)
        end_work_time = cls._adjust_time_with_tolerance(WORK_END, TOLERANCE)

        if start_date.time() < start_work_time:
            start_date = start_date.replace(
                hour=start_work_time.hour,
                minute=start_work_time.minute,
                second=start_work_time.second,
            )
        if end_date.time() > end_work_time:
            end_date = end_date.replace(
                hour=end_work_time.hour,
                minute=end_work_time.minute,
                second=end_work_time.second,
            )

        return start_date, end_date

    @classmethod
    def calculate_work_hours(cls, start_date: datetime, end_date: datetime) -> float:
        """
        Рассчитывает количество рабочих часов между двумя датами.

        Args:
            start_date: Начальная дата
            end_date: Конечная дата

        Returns:
            Количество рабочих часов
        """

        # Рассчитываем количество рабочих часов в день
        work_hours_per_day = (WORK_END.hour + WORK_END.minute / 60) - (
            WORK_START.hour + WORK_START.minute / 60
        )

        # Рассчитываем количество дней между датами (исключая выходные, если нужно)
        current_date = start_date.date()
        end_date_day = end_date.date()
        days = 0

        while current_date <= end_date_day:
            # Проверяем, является ли день рабочим (не выходным)
            # Можно добавить проверку на выходные, если нужно
            days += 1
            current_date += timedelta(days=1)

        return days * work_hours_per_day
