from datetime import datetime, time, timedelta
from typing import Optional, Tuple

from constants.work_time import END_TIME, START_TIME, TOLERANCE
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
            base_time=work_start or START_TIME,
            delta=-(tolerance or TOLERANCE),
        )
        end_with_tolerance = WorkTimeService._adjust_time_with_tolerance(
            base_time=work_end or END_TIME,
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
        start_work_time = cls._adjust_time_with_tolerance(START_TIME, -TOLERANCE)
        end_work_time = cls._adjust_time_with_tolerance(END_TIME, TOLERANCE)

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
        *,
        work_start: time,
        work_end: time,
        tolerance: int,
    ) -> Tuple[datetime, datetime]:
        """
        Корректирует даты начала и конца в соответствии с рабочими часами и допустимым отклонением.

        Если время начала раньше рабочего времени (с учетом допуска),
        устанавливает его на начало рабочего времени.
        Если время окончания позже рабочего времени (с учетом допуска),
        устанавливает его на конец рабочего времени.

            Args:
                start_date: Дата и время начала
                end_date: Дата и время окончания
                work_start: Начало рабочего времени
                work_end: Конец рабочего времени
                tolerance: Допустимое отклонение в минутах
            Returns:
                Кортеж из скорректированных дат начала и окончания
        """
        start_work_time = cls._adjust_time_with_tolerance(
            base_time=work_start,
            delta=-tolerance,
        )
        end_work_time = cls._adjust_time_with_tolerance(
            base_time=work_end,
            delta=tolerance,
        )

        start_date = start_date.replace(
            hour=start_work_time.hour,
            minute=start_work_time.minute,
            second=start_work_time.second,
        )
        end_date = end_date.replace(
            hour=end_work_time.hour,
            minute=end_work_time.minute,
            second=end_work_time.second,
        )

        return start_date, end_date

    @classmethod
    def calculate_work_hours(
        cls,
        start_date: datetime,
        end_date: datetime,
        work_start: Optional[time] = None,
        work_end: Optional[time] = None,
    ) -> float:
        """
        Рассчитывает количество рабочих часов между двумя датами.

        Учитывает только рабочие часы в каждом дне в заданном промежутке.

        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            work_start: Начало рабочего времени (по умолчанию START_TIME)
            work_end: Конец рабочего времени (по умолчанию END_TIME)

        Returns:
            Количество рабочих часов, округленное до 2 знаков после запятой
        """
        # Проверяем корректность дат
        if start_date > end_date:
            return 0.0

        # Убедимся, что обе даты имеют одинаковый тип (с часовым поясом или без)
        if start_date.tzinfo is not None and end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=start_date.tzinfo)
        elif start_date.tzinfo is None and end_date.tzinfo is not None:
            start_date = start_date.replace(tzinfo=end_date.tzinfo)

        # Используем переданные или глобальные границы рабочего времени
        work_start_time = work_start or START_TIME
        work_end_time = work_end or END_TIME

        # Рассчитываем количество рабочих часов в полном рабочем дне
        work_hours_per_day = (work_end_time.hour + work_end_time.minute / 60) - (
            work_start_time.hour + work_start_time.minute / 60
        )
        work_hours_per_day = round(work_hours_per_day, 2)

        # Если даты в одном дне
        if start_date.date() == end_date.date():
            return cls._calculate_work_hours_in_day(
                start_date, end_date, work_start_time, work_end_time
            )

        # Рассчитываем часы для первого дня (от start_date до конца рабочего дня)
        first_day_end = datetime.combine(start_date.date(), work_end_time)
        if start_date.tzinfo is not None:
            first_day_end = first_day_end.replace(tzinfo=start_date.tzinfo)
        first_day_hours = cls._calculate_work_hours_in_day(
            start_date, first_day_end, work_start_time, work_end_time
        )

        # Рассчитываем часы для последнего дня (от начала рабочего дня до end_date)
        last_day_start = datetime.combine(end_date.date(), work_start_time)
        if end_date.tzinfo is not None:
            last_day_start = last_day_start.replace(tzinfo=end_date.tzinfo)
        last_day_hours = cls._calculate_work_hours_in_day(
            last_day_start, end_date, work_start_time, work_end_time
        )

        # Рассчитываем количество полных рабочих дней между первым и последним днем
        full_days = (end_date.date() - start_date.date()).days - 1
        if full_days < 0:
            full_days = 0

        # Суммируем все часы и округляем до 2 знаков
        total_hours = (
            first_day_hours + (full_days * work_hours_per_day) + last_day_hours
        )
        total_hours = round(total_hours, 2)

        return total_hours

    @classmethod
    def _calculate_work_hours_in_day(
        cls,
        start_datetime: datetime,
        end_datetime: datetime,
        work_start_time: time,
        work_end_time: time,
    ) -> float:
        """
        Рассчитывает количество рабочих часов в пределах одного дня.

        Args:
            start_datetime: Начальное время
            end_datetime: Конечное время
            work_start_time: Начало рабочего дня
            work_end_time: Конец рабочего дня

        Returns:
            Количество рабочих часов, округленное до 2 знаков после запятой
        """
        # Проверяем, что даты в одном дне
        if start_datetime.date() != end_datetime.date():
            raise ValueError("Даты должны быть в одном дне")

        # Ограничиваем время рабочими часами
        day_start = datetime.combine(start_datetime.date(), work_start_time)
        day_end = datetime.combine(end_datetime.date(), work_end_time)

        # Сохраняем информацию о часовом поясе
        if start_datetime.tzinfo is not None:
            day_start = day_start.replace(tzinfo=start_datetime.tzinfo)
            day_end = day_end.replace(tzinfo=start_datetime.tzinfo)

        # Если начало после конца рабочего дня или конец до начала рабочего дня
        if start_datetime > day_end or end_datetime < day_start:
            return 0.0

        # Корректируем границы
        effective_start = max(start_datetime, day_start)
        effective_end = min(end_datetime, day_end)

        # Рассчитываем часы и округляем до 2 знаков
        hours = (effective_end - effective_start).total_seconds() / 3600
        hours = round(hours, 2)

        return max(0.0, hours)
