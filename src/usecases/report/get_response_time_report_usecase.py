from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from statistics import mean, median
from typing import Optional

from dto.report import ResponseTimeReportDTO
from exceptions.user import UserNotFoundException
from models import MessageReply, User
from repositories import MessageReplyRepository, MessageRepository, UserRepository
from services.time_service import TimeZoneService
from utils.formatter import format_seconds, format_selected_period


@dataclass
class Report:
    text: str
    chart: Optional[str] = None
    excel: Optional[str] = None


class GetResponseTimeReportUseCase:
    """UseCase для генерации отчетов о времени ответа пользователей.

    Attributes:
        _msg_reply_repository: Репозиторий для работы с ответами
        _user_repository: Репозиторий для работы с пользователями
    """

    def __init__(
        self,
        msg_reply_repository: MessageReplyRepository,
        msg_repository: MessageRepository,
        user_repository: UserRepository,
    ):
        self._msg_reply_repository = msg_reply_repository
        self._user_repository = user_repository
        self._msg_repository = msg_repository

    async def execute(self, report_dto: ResponseTimeReportDTO) -> Report:
        user = await self._user_repository.get_user_by_username(
            username=report_dto.username
        )

        if not user:
            raise UserNotFoundException()

        # Получаем все reply сообщения за нужный период из БД
        msg_replies = await self._msg_reply_repository.get_replies_by_period_date(
            user_id=user.id,
            start_date=report_dto.start_date,
            end_date=report_dto.end_date,
        )

        msgs = await self._msg_repository.get_messages_by_period_date(
            user_id=user.id,
            start_date=report_dto.start_date,
            end_date=report_dto.end_date,
        )

        return self._generate_report(
            replies=msg_replies,
            messages=msgs,
            user=user,
            start_date=report_dto.start_date,
            end_date=report_dto.end_date,
            selected_period=report_dto.selected_period,
        )

    def _generate_report(
        self,
        replies: list[MessageReply],
        messages: list[MessageReply],
        user: User,
        start_date: datetime,
        end_date: datetime,
        selected_period: str = None,
    ) -> Report:
        """
        Формирует текстовый отчет о времени ответа в заданном формате.
        """
        period = format_selected_period(selected_period)

        if not replies:
            return Report(
                text=(
                    f"Отчёт: @{user.username} за {period}\n\n"
                    "⚠️ Нет данных за указанный период."
                )
            )

        # Собираем статистику по времени ответа
        response_times = [reply.response_time_seconds for reply in replies]

        # # Группируем по чатам
        # chat_stats = defaultdict(list)
        # for reply in replies:
        #     chat_title = (
        #         reply.chat_session.title
        #         if hasattr(reply, "chat_session") and reply.chat_session.title
        #         else "Без названия"
        #     )
        #     chat_stats[chat_title].append(reply.response_time_seconds)

        # Рассчитываем статистику
        avg_time = mean(response_times)
        median_time = median(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        total_replies = len(replies)
        time_first_replie = TimeZoneService.convert_to_local_time(
            replies[0].created_at
        ).strftime("%H:%M")

        total_messages = len(messages)
        messages_per_hour = self._messages_per_hour(len(messages), start_date, end_date)
        time_first_message = TimeZoneService.convert_to_local_time(
            messages[0].created_at
        ).strftime("%H:%M")

        # Форматируем отчет
        report = (
            f"<b>📊 Отчёт: @{user.username} за {period}</b>\n\n"
            # f"<b>🕒 Временной период:</b> {start_date.strftime('%d.%m.%Y')}-"
            # f"{end_date.strftime('%d.%m.%Y')} "
            # f"({start_date.strftime('%H:%M')}-{end_date.strftime('%H:%M')})\n\n"
            f"<b>📈 Статистика по сообщениям:</b>\n"
            f"• <b>{total_messages}</b> - всего сообщений\n"
            f"• <b>{messages_per_hour}</b> - сообщений в час\n"
            f"• <b>{time_first_message}</b> - время первого сообщения\n"
        )

        # report += "По чатам:\n"

        # # Добавляем статистику по чатам
        # for chat_title, times in sorted(chat_stats.items(), key=lambda x: -len(x[1])):
        #     # Получаем количество сообщений для данного чата
        #     chat_messages = sum(
        #         1
        #         for msg in messages
        #         if (
        #             hasattr(msg, "chat_session")
        #             and msg.chat_session.title == chat_title
        #         )
        #         or (not hasattr(msg, "chat_session") and chat_title == "Без названия")
        #     )
        #     chat_avg = mean(times)
        #     report += (
        #         f"<b>{chat_title}</b> — <b>{chat_messages}</b> сообщ. "
        #         f"(<b>{self._format_seconds(chat_avg)}</b> - частота отпр)\n"
        #     )

        # Добавляем общую статистику по времени ответа
        report += (
            f"\n<b>⏱️ Статистика по ответам:</b>\n"
            f"• <b>{total_replies}</b> - всего ответов\n"
            f"• <b>{time_first_replie}</b> - время первого ответа\n"
            f"• <b>{format_seconds(min_time)}</b> и "
            f"<b>{format_seconds(max_time)}</b> - мин. и макс. время ответов\n"
            f"• <b>{format_seconds(avg_time)}</b> и "
            f"<b>{format_seconds(median_time)}</b> - сред. и медиан. время ответа\n"
        )

        return Report(text=report)

    def _messages_per_hour(
        self,
        messages_count: int,
        start_date: datetime,
        end_date: datetime,
    ) -> float:
        """
        Рассчитывает количество сообщений в час.
        """
        if messages_count < 2:
            return 1
        hours = (end_date - start_date).total_seconds() / 3600
        if hours <= 0:
            return 1
        return round(messages_count / hours, 2)
