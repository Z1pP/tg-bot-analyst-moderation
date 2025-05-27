from collections import defaultdict
from datetime import datetime
from statistics import mean, median

from dto.report import ResponseTimeReportDTO
from exceptions.user import UserNotFoundException
from models import MessageReply, User
from repositories.message_reply_repository import MessageReplyRepository
from repositories.user_repository import UserRepository
from services.time_service import TimeZoneService


class Report:
    text: str
    chart: str
    excel: str


class GetResponseTimeReportUseCase:
    """UseCase для генерации отчетов о времени ответа пользователей.

    Attributes:
        _msg_reply_repository: Репозиторий для работы с ответами
        _user_repository: Репозиторий для работы с пользователями
    """

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

        msg_replies = await self._msg_reply_repository.get_replies_by_user_and_period(
            user_id=user.id,
            start_date=report_dto.start_date,
            end_date=report_dto.end_date,
        )

        return self._generate_report(
            replies=msg_replies,
            user=user,
            start_date=report_dto.start_date,
            end_date=report_dto.end_date,
            selected_period=report_dto.selected_period,
        )

    def _generate_report(
        self,
        replies: list[MessageReply],
        user: User,
        start_date: datetime,
        end_date: datetime,
        selected_period: str = None,
    ) -> str:
        """
        Формирует текстовый отчет о времени ответа в заданном формате.
        """
        period = self._format_selected_period(selected_period)

        if not replies:
            return f"Отчёт: @{user.username} за {period}\n\n⚠️ Нет данных за указанный период."

        # Собираем статистику по времени ответа
        response_times = [reply.response_time_seconds for reply in replies]

        # Группируем по чатам
        chat_stats = defaultdict(list)
        for reply in replies:
            chat_title = (
                reply.chat_session.title
                if hasattr(reply, "chat_session") and reply.chat_session.title
                else "Без названия"
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
            f"Отчёт: @{user.username} за {period}\n\n"
            f"Временной период: {start_date.strftime('%d.%m.%Y')}-{end_date.strftime('%d.%m.%Y')}\n"
            f"📊 Всего ответов — <b>{total_replies}</b>\n"
        )

        # Добавляем статистику по чатам
        for chat_title, times in sorted(chat_stats.items(), key=lambda x: -len(x[1])):
            chat_count = len(times)
            chat_avg = mean(times)
            report += (
                f"В чате <b>{chat_title}</b> — <b>{chat_count}</b> "
                f"- ср. время отв. — <b>{self._format_seconds(chat_avg)}</b>\n"
            )

        # Добавляем общую статистику по времени ответа
        report += (
            f"\n⏱️ Время ответа:\n"
            f"Min|max ответ: <b>{self._format_seconds(min_time)}</b> и "
            f"<b>{self._format_seconds(max_time)}</b>\n"
            f"AVG и медиан. ответ: <b>{self._format_seconds(avg_time)}</b> и "
            f"<b>{self._format_seconds(median_time)}</b>\n\n"
            f"<i>Отчет сгенерирован: {TimeZoneService.now().strftime('%d.%m.%Y %H:%M')}</i>"
        )

        return report

    def _format_selected_period(self, selected_period: str) -> str:
        """
        Форматирует выбранный период в читаемый формат.
        """
        if not selected_period:
            return "указанный период"
        period = selected_period.split("За")[-1]
        return period.strip()

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
