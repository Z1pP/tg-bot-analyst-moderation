from datetime import datetime
from statistics import mean
from typing import List, Tuple

from constants import BREAK_TIME
from dto.report import BreakDayDTO, BreakIntervalDTO
from models import ChatMessage, MessageReaction
from services.time_service import TimeZoneService
from utils.formatter import format_seconds


class BreakAnalysisService:
    """Сервис для анализа перерывов в сообщениях с учетом реакций."""

    @classmethod
    def calculate_breaks(
        cls,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        min_break_minutes: int = BREAK_TIME,
        is_single_day: bool = False,
    ) -> List[str]:
        """
        Считает перерывы между активностью (сообщения + реакции) в пределах одного дня.

        Args:
            messages: Список сообщений
            reactions: Список реакций на сообщения
            min_break_minutes: Минимальная продолжительность перерыва в минутах

        Returns:
            Список строк с информацией о перерывах
        """
        # Объединяем сообщения и реакции в единый список активности
        activities = cls._merge_activities(messages, reactions)

        if len(activities) < 2:
            return []

        result = []
        # Группируем активность по дате
        activities_by_date = {}

        for activity_time, activity_type in activities:
            local_time = TimeZoneService.convert_to_local_time(activity_time)
            date_key = local_time.date()
            if date_key not in activities_by_date:
                activities_by_date[date_key] = []
            activities_by_date[date_key].append((local_time, activity_type))

        # Обрабатываем каждый день отдельно
        for date, day_activities in sorted(activities_by_date.items()):
            day_activities.sort(key=lambda x: x[0])
            day_breaks = []
            total_break_time = 0

            # Ищем перерывы в пределах одного дня
            for i in range(1, len(day_activities)):
                prev_time, _ = day_activities[i - 1]
                curr_time, _ = day_activities[i]

                minutes_diff = (curr_time - prev_time).total_seconds() / 60

                if minutes_diff >= min_break_minutes:
                    start_break = prev_time.strftime("%H:%M")
                    end_break = curr_time.strftime("%H:%M")
                    day_breaks.append(
                        f"{start_break}-{end_break} - {int(minutes_diff)} мин."
                    )
                    total_break_time += minutes_diff

            # Добавляем информацию о дне, если есть перерывы
            if day_breaks:
                date_str = date.strftime("%d.%m.%Y")
                total_formatted = cls._format_break_time(total_break_time)

                if not is_single_day:
                    result.append(f"<code>{date_str}</code>")
                result.append(
                    f"<b>{total_formatted}</b> - общее время перерыва за день"
                )
                result.extend([f"• {br}" for br in day_breaks])
                result.append("")

        return result

    @classmethod
    def calculate_breaks_structured(
        cls,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        min_break_minutes: int = BREAK_TIME,
    ) -> List[BreakDayDTO]:
        """
        Возвращает структурированные перерывы по дням без форматирования строк.
        """
        activities = cls._merge_activities(messages, reactions)

        if len(activities) < 2:
            return []

        activities_by_date = {}
        for activity_time, activity_type in activities:
            local_time = TimeZoneService.convert_to_local_time(activity_time)
            date_key = local_time.date()
            if date_key not in activities_by_date:
                activities_by_date[date_key] = []
            activities_by_date[date_key].append((local_time, activity_type))

        result: List[BreakDayDTO] = []
        for date, day_activities in sorted(activities_by_date.items()):
            day_activities.sort(key=lambda x: x[0])
            intervals: List[BreakIntervalDTO] = []
            total_break_minutes = 0

            for i in range(1, len(day_activities)):
                prev_time, _ = day_activities[i - 1]
                curr_time, _ = day_activities[i]
                minutes_diff = (curr_time - prev_time).total_seconds() / 60

                if minutes_diff >= min_break_minutes:
                    intervals.append(
                        BreakIntervalDTO(
                            start_time=prev_time.strftime("%H:%M"),
                            end_time=curr_time.strftime("%H:%M"),
                            duration_minutes=int(minutes_diff),
                        )
                    )
                    total_break_minutes += minutes_diff

            if intervals:
                result.append(
                    BreakDayDTO(
                        date=datetime.combine(date, datetime.min.time()),
                        total_break_seconds=int(total_break_minutes * 60),
                        intervals=intervals,
                    )
                )

        return result

    @classmethod
    def avg_breaks_time(
        cls,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        min_break_minutes: int = BREAK_TIME,
    ) -> str:
        """Считает среднее время перерыва между сообщениями и реакциями"""
        activities = cls._merge_activities(messages, reactions)

        if len(activities) < 2:
            return ""

        break_durations = []

        for i in range(1, len(activities)):
            prev_time = activities[i - 1][0]
            curr_time = activities[i][0]

            break_seconds = (curr_time - prev_time).total_seconds()

            if break_seconds >= min_break_minutes * 60:
                break_durations.append(break_seconds)

        if not break_durations:
            return ""

        avg_break_seconds = mean(break_durations)
        return format_seconds(int(avg_break_seconds))

    @classmethod
    def total_breaks_time_per_day(
        cls,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        min_break_minutes: int = BREAK_TIME,
    ) -> List[float]:
        """Возвращает список общего времени перерывов за каждый день в минутах."""
        activities = cls._merge_activities(messages, reactions)

        if len(activities) < 2:
            return []

        activities_by_date = {}
        for activity_time, _ in activities:
            local_time = TimeZoneService.convert_to_local_time(activity_time)
            date_key = local_time.date()
            if date_key not in activities_by_date:
                activities_by_date[date_key] = []
            activities_by_date[date_key].append(local_time)

        daily_totals = []
        for _, day_activities in sorted(activities_by_date.items()):
            day_activities.sort()
            day_total = 0
            for i in range(1, len(day_activities)):
                diff = (day_activities[i] - day_activities[i - 1]).total_seconds() / 60
                if diff >= min_break_minutes:
                    day_total += diff
            if day_total > 0:
                daily_totals.append(day_total)

        return daily_totals

    @classmethod
    def _merge_activities(
        cls, messages: List[ChatMessage], reactions: List[MessageReaction]
    ) -> List[Tuple[datetime, str]]:
        """
        Объединяет сообщения и реакции в единый список активности.

        Returns:
            Список кортежей (время, тип_активности)
        """
        activities = []

        # Добавляем сообщения
        for msg in messages:
            activities.append((msg.created_at, "message"))

        # Добавляем реакции
        for reaction in reactions:
            activities.append((reaction.created_at, "reaction"))

        # Сортируем по времени
        activities.sort(key=lambda x: x[0])
        return activities

    @classmethod
    def _format_break_time(cls, minutes: float) -> str:
        """Форматирует время перерыва из минут в читаемый формат."""
        return format_seconds(seconds=minutes * 60)
