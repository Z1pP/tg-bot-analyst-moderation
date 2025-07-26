from typing import List

from constants import BREAK_TIME
from models import ChatMessage
from services.time_service import TimeZoneService
from utils.formatter import format_seconds


class BreakAnalysisService:
    """Сервис для анализа перерывов в сообщениях."""

    @classmethod
    def calculate_breaks(
        cls, messages: List[ChatMessage], min_break_minutes: int = BREAK_TIME
    ) -> List[str]:
        """
        Считает перерывы между сообщениями в пределах одного дня.

        Args:
            messages: Список сообщений
            min_break_minutes: Минимальная продолжительность перерыва в минутах

        Returns:
            Список строк с информацией о перерывах
        """
        if len(messages) < 2:
            return []

        result = []
        # Группируем сообщения по дате
        messages_by_date = {}

        for msg in messages:
            local_time = TimeZoneService.convert_to_local_time(msg.created_at)
            date_key = local_time.date()
            if date_key not in messages_by_date:
                messages_by_date[date_key] = []
            messages_by_date[date_key].append((local_time, msg))

        # Обрабатываем каждый день отдельно
        for date, day_messages in sorted(messages_by_date.items()):
            day_messages.sort(key=lambda x: x[0])
            day_breaks = []
            total_break_time = 0

            # Ищем перерывы в пределах одного дня
            for i in range(1, len(day_messages)):
                prev_time, prev_msg = day_messages[i - 1]
                curr_time, curr_msg = day_messages[i]

                minutes_diff = (curr_time - prev_time).total_seconds() / 60

                if minutes_diff >= min_break_minutes:
                    start_break = prev_time.strftime("%H:%M")
                    end_break = curr_time.strftime("%H:%M")
                    day_breaks.append(
                        f"{start_break}-{end_break} -- {int(minutes_diff)} мин."
                    )
                    total_break_time += minutes_diff

            # Добавляем информацию о дне, если есть перерывы
            if day_breaks:
                date_str = date.strftime("%d.%m.%Y")
                # avg_break = round(total_break_time / len(day_breaks), 1)
                total_formatted = cls._format_break_time(total_break_time)

                result.append(f"<code>{date_str}</code>")
                result.append(
                    f"<b>{total_formatted}</b> - общее время перерыва за день"
                )
                result.extend([f"• {br}" for br in day_breaks])
                result.append("")

        return result

    def _format_break_time(minutes: float) -> str:
        """Форматирует время перерыва из минут в читаемый формат."""
        return format_seconds(seconds=minutes * 60)
