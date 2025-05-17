import logging
from datetime import datetime, timedelta
from typing import Tuple

from dto.report import AVGReportDTO
from models import ChatMessage, User
from repositories import MessageRepository, UserRepository

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
        try:
            user = await self._user_repository.get_user_by_username(report_dto.username)
            if not user:
                return "❌ Пользователь не найден в базе данных."

            start_date, end_date = self._get_period(report_dto.time)
            messages = await self._message_repository.get_messages_by_period_date(
                user_id=user.id,
                start_date=start_date,
                end_date=end_date,
            )

            return self._generate_report(
                messages=messages, user=user, time_period=report_dto.time
            )
        except Exception as e:
            logger.error(f"Ошибка при формировании отчета: {e}")
            return f"Произошла ошибка при формировании отчета: {e}"

    def _generate_report(
        self,
        messages: list[ChatMessage],
        user: User,
        time_period: timedelta,
    ) -> str:
        """
        Формирует текстовый отчет.
        """
        if not messages:
            return "❌ Нет данных для формирования отчета."

        total_messages = len(messages)
        period_str = self._format_timedelta(time_period)
        start_date, end_date = self._get_period(time_period)

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

        return (
            f"📊 <b>Отчет за {period_str}</b>\n"
            f"⏱ Период: <b>{date_range}</b>\n"
            f"👤 Пользователь: <b>{user.username}</b>\n\n"
            f"📈 Статистика:\n"
            f"• Всего сообщений: <b>{total_messages}</b>\n"
            f"• Среднее за {period_str}: <b>{avg}</b> сообщ./{unit}\n\n"
            f"<i>Отчет сгенерирован {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>"
        )

    def _get_period(self, time: timedelta) -> Tuple[datetime, datetime]:
        """
        Возвращает начальную и конечную дату для отчета.
        """
        end_date = datetime.now()
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
