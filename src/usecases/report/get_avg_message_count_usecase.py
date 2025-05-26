import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Tuple

from dto.report import AVGReportDTO
from exceptions.user import UserNotFoundException
from models import ChatMessage, User
from repositories import MessageRepository, UserRepository
from services.time_service import TimeZoneService

logger = logging.getLogger(__name__)


class GetAvgMessageCountUseCase:
    def __init__(
        self,
        message_repository: MessageRepository,
        user_repository: UserRepository,
    ):
        self._message_repository = message_repository
        self._user_repository = user_repository

    async def execute(self, report_dto: AVGReportDTO) -> str:
        """
        Формирует отчет о среднем количестве сообщений пользователя за указанный период.
        """
        user = await self._user_repository.get_user_by_username(
            username=report_dto.username
        )
        if not user:
            raise UserNotFoundException()

        messages = await self._message_repository.get_messages_by_period_date(
            user_id=user.id,
            start_date=report_dto.start_date,
            end_date=report_dto.end_date,
        )

        return self._generate_report(
            messages=messages,
            user=user,
            start_date=report_dto.start_date,
            end_date=report_dto.end_date,
            selected_period=report_dto.selected_period,
        )

    def _generate_report(
        self,
        messages: list[ChatMessage],
        user: User,
        start_date: datetime,
        end_date: datetime,
        selected_period: str = None,
    ) -> str:
        """
        Формирует текстовой отчет.
        """
        if not messages:
            return "❌ Нет данных для формирования отчета."

        total_messages = len(messages)
        period_str = selected_period if selected_period else "выбранное"
        time_period = end_date - start_date

        # Группируем сообщения по чатам
        chat_stats = defaultdict(int)
        for message in messages:
            chat_title = message.chat_session.title
            chat_stats[chat_title] += 1

        # Определяем единицу измерения для среднего значения
        if time_period.total_seconds() <= 3600:  # До 1 часа
            avg = round(total_messages / (time_period.total_seconds() / 3600), 2)
            unit = "час"
        elif time_period.total_seconds() <= 86400:  # До 1 дня
            avg = round(total_messages / (time_period.total_seconds() / 3600), 2)
            unit = "час"
        else:  # Более 1 дня
            avg = round(total_messages / (time_period.total_seconds() / 86400), 2)
            unit = "день"

        date_range = (
            f"{start_date.strftime('%d.%m.%Y %H:%M')} - "
            f"{end_date.strftime('%d.%m.%Y %H:%M')}"
        )

        # Формируем основную часть отчета
        report = (
            f"📊 <b>Отчет за {period_str}</b>\n"
            f"⏱ Период: <b>{date_range}</b>\n"
            f"👤 Пользователь: <b>{user.username}</b>\n\n"
            f"📈 Общая статистика:\n"
            f"• Всего сообщений: <b>{total_messages}</b>\n"
            f"• Среднее за {period_str}: <b>{avg}</b> сообщ./{unit}\n"
            f"────────────────────────────\n"
        )

        # Добавляем статистику по чатам
        report += "\n📊 <b>Статистика по чатам:</b>\n"
        for chat_title, count in sorted(
            chat_stats.items(), key=lambda x: x[1], reverse=True
        ):
            # Вычисляем среднее для каждого чата
            if time_period.total_seconds() <= 86400:  # До 1 дня
                chat_avg = round(count / (time_period.total_seconds() / 3600), 2)
                chat_unit = "час"
            else:  # Более 1 дня
                chat_avg = round(count / (time_period.total_seconds() / 86400), 2)
                chat_unit = "день"

            report += f"  • «{chat_title}» — <b>{count}</b> сообщ. (<b>{chat_avg}</b> сообщ./{chat_unit})\n"

        report += "────────────────────────────\n"
        report += f"<i>Отчет сгенерирован {TimeZoneService.now().strftime('%d.%m.%Y %H:%M')}</i>"

        return report

    def _get_period(self, time: timedelta) -> Tuple[datetime, datetime]:
        """
        Возвращает начальную и конечную дату для отчета.
        """
        end_date = TimeZoneService.now()
        start_date = end_date - time
        return start_date, end_date

    def _format_timedelta(self, td: timedelta) -> str:
        """
        Форматирует timedelta в читаемый текст на русском.
        """
        total_seconds = td.total_seconds()

        if total_seconds < 3600:
            minutes = int(total_seconds / 60)
            return f"{minutes} {self._pluralize(minutes, 'минута', 'минуты', 'минут')}"
        if total_seconds < 86400:
            hours = int(total_seconds / 3600)
            return f"{hours} {self._pluralize(hours, 'час', 'часа', 'часов')}"
        days = td.days
        if days < 7:
            return f"{days} {self._pluralize(days, 'день', 'дня', 'дней')}"
        if days < 30:
            weeks = days // 7
            return f"{weeks} {self._pluralize(weeks, 'неделя', 'недели', 'недель')}"
        months = days // 30
        return f"{months} {self._pluralize(months, 'месяц', 'месяца', 'месяцев')}"

    def _pluralize(self, n: int, form1: str, form2: str, form5: str) -> str:
        """
        Склоняет существительные в зависимости от числа.
        """
        n = abs(n) % 100
        if 10 < n < 20:
            return form5
        n %= 10
        if n == 1:
            return form1
        if 2 <= n <= 4:
            return form2
        return form5
