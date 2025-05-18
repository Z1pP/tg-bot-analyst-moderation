from collections import defaultdict
from datetime import datetime, time
from statistics import mean, median

from dto.report import ResponseTimeReportDTO
from exceptions.user import UserNotFoundException
from models import MessageReply, User
from repositories.message_reply_repository import MessageReplyRepository
from repositories.user_repository import UserRepository


class GetResponseTimeReportUseCase:
    def __init__(
        self,
        msg_reply_repository: MessageReplyRepository,
        user_repository: UserRepository,
    ):
        self._msg_reply_repository = msg_reply_repository
        self._user_repository = user_repository

    async def execute(self, report_dto: ResponseTimeReportDTO) -> str:
        user = await self._user_repository.get_user_by_username(
            username=report_dto.username
        )

        if not user:
            raise UserNotFoundException()

        start_date, end_date = self._get_period(report_date=report_dto.report_date)

        msg_replies = await self._msg_reply_repository.get_replies_by_user_and_period(
            user_id=user.id,
            start_date=start_date,
            end_date=end_date,
        )

        return self._generate_report(
            replies=msg_replies,
            user=user,
            report_date=report_dto.report_date or datetime.now().date(),
        )

    def _get_period(self, report_date=None) -> tuple[datetime, datetime]:
        """
        Получает период для отчета - весь указанный день.
        Если дата не указана, используется текущий день.

        Args:
            report_date: Дата отчета (опционально)

        Returns:
            tuple: (начало дня, конец дня)
        """
        # Если дата не указана, используем текущую
        if report_date is None:
            report_date = datetime.now().date()

        # Начало дня (00:00:00)
        start_date = datetime.combine(report_date, time.min)

        # Конец дня (23:59:59)
        end_date = datetime.combine(report_date, time.max)

        return start_date, end_date

    def _generate_report(
        self,
        replies: list[MessageReply],
        user: User,
        report_date: datetime.date,
    ) -> str:
        """
        Формирует текстовый отчет о времени ответа.
        """
        if not replies:
            return (
                f"⚠️ <b>Отчет о времени ответа</b>\n\n"
                f"Нет данных за {report_date.strftime('%d.%m.%Y')}."
            )

        # Собираем статистику по времени ответа
        response_times = [reply.response_time_seconds for reply in replies]

        # Группируем по чатам
        chat_stats = defaultdict(list)
        for reply in replies:
            chat_title = (
                reply.chat_session.title
                if hasattr(reply, "chat_session")
                else "Неизвестный чат"
            )
            chat_stats[chat_title].append(reply.response_time_seconds)

        # Рассчитываем статистику
        avg_time = mean(response_times)
        median_time = median(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        total_replies = len(replies)

        # Форматируем отчет
        report = (
            f"⏱ <b>Отчет о времени ответа</b>\n"
            f"👤 Пользователь: <b>{user.username}</b>\n"
            f"📅 Дата: <b>{report_date.strftime('%d.%m.%Y')}</b>\n\n"
            f"📊 <b>Общая статистика:</b>\n"
            f"• Всего ответов: <b>{total_replies}</b>\n"
            f"• Среднее время ответа: <b>{self._format_seconds(avg_time)}</b>\n"
            f"• Медианное время: <b>{self._format_seconds(median_time)}</b>\n"
            f"• Минимальное время: <b>{self._format_seconds(min_time)}</b>\n"
            f"• Максимальное время: <b>{self._format_seconds(max_time)}</b>\n"
            f"────────────────────────────\n\n"
        )

        # Добавляем статистику по чатам
        report += "<b>📊 Статистика по чатам:</b>\n"
        for chat_title, times in sorted(chat_stats.items(), key=lambda x: mean(x[1])):
            chat_avg = mean(times)
            chat_count = len(times)
            report += f"• «{chat_title}» — <b>{chat_count}</b> ответов, среднее время: <b>{self._format_seconds(chat_avg)}</b>\n"

        report += (
            f"\n<i>Отчет сгенерирован {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>"
        )

        return report

    def _format_seconds(self, seconds: float) -> str:
        """
        Форматирует секунды в читаемый формат.
        """
        if seconds < 60:
            return f"{round(seconds, 1)} сек."
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{round(minutes, 1)} мин."
        else:
            hours = seconds / 3600
            return f"{round(hours, 1)} ч."
