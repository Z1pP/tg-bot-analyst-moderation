from typing import List

from models import ChatMessage
from services.time_service import TimeZoneService


class BreakAnalysisService:
    """Сервис для анализа перерывов в сообщениях."""

    @classmethod
    def calculate_breaks(
        cls, messages: List[ChatMessage], min_break_minutes: int = 30
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

        breaks = []
        # Группируем сообщения по дате
        messages_by_date = {}

        for msg in messages:
            local_time = TimeZoneService.convert_to_local_time(msg.created_at)
            date_key = local_time.date()
            if date_key not in messages_by_date:
                messages_by_date[date_key] = []
            messages_by_date[date_key].append((local_time, msg))

        # Обрабатываем каждый день отдельно
        for date, day_messages in messages_by_date.items():
            # Сортируем сообщения по времени
            day_messages.sort(key=lambda x: x[0])

            # Ищем перерывы в пределах одного дня
            for i in range(1, len(day_messages)):
                prev_time, prev_msg = day_messages[i - 1]
                curr_time, curr_msg = day_messages[i]

                minutes_diff = (curr_time - prev_time).total_seconds() / 60

                if minutes_diff >= min_break_minutes:
                    start_break = prev_time.strftime("%H:%M")
                    end_break = curr_time.strftime("%H:%M")
                    date_str = prev_time.strftime("%d.%m.%Y")
                    breaks.append(
                        f"{start_break}-{end_break} — {round(minutes_diff)} мин. ({date_str})"
                    )

        return breaks
