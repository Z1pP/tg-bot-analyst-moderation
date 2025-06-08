from dataclasses import dataclass
from datetime import datetime
from statistics import mean, median
from typing import Optional

from dto.report import ResponseTimeReportDTO
from exceptions.user import UserNotFoundException
from models import ChatMessage, MessageReply, User
from repositories import MessageReplyRepository, MessageRepository, UserRepository
from services.time_service import TimeZoneService
from utils.formatter import format_seconds, format_selected_period


@dataclass
class Report:
    text: str
    chart: Optional[str] = None
    excel: Optional[str] = None


class GetResponseTimeReportUseCase:
    """UseCase для генерации отчетов о времени ответа пользователей."""

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

        # Получаем сообщения и ответы за указанный период
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
        messages: list[ChatMessage],
        user: User,
        start_date: datetime,
        end_date: datetime,
        selected_period: str = None,
    ) -> Report:
        """Формирует текстовый отчет о времени ответа."""
        period = format_selected_period(selected_period)

        if not messages:
            return Report(
                text=(
                    f"<b>📊 Отчёт: @{user.username} за {period}</b>\n\n"
                    "⚠️ Нет данных за указанный период."
                )
            )

        # Сортируем сообщения по времени
        sorted_messages = sorted(messages, key=lambda r: r.created_at)

        # Собираем статистику
        response_times = (
            [reply.response_time_seconds for reply in replies] if replies else [0]
        )
        total_messages = len(messages)
        total_replies = len(replies)

        # Рассчитываем статистику времени ответа
        if response_times:
            avg_time = mean(response_times)
            median_time = median(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
        else:
            avg_time = median_time = min_time = max_time = 0

        # Рассчитываем сообщения в час и время первого сообщения
        messages_per_hour = self._messages_per_hour(
            total_messages, start_date, end_date
        )
        time_first_message = (
            TimeZoneService.convert_to_local_time(
                sorted_messages[0].created_at
            ).strftime("%H:%M")
            if sorted_messages
            else "N/A"
        )

        # Формируем отчет
        report_lines = [
            f"<b>📊 Отчёт: @{user.username} за {period}</b>\n",
            f"• <b>{time_first_message}</b> - время первого сообщения\n",
            f"• <b>{total_messages}</b> - всего сообщений",
            f"• <b>{messages_per_hour}</b> - сообщений в час",
            f"• Из них <b>{total_replies}</b> ответов",
        ]

        # Добавляем статистику по времени ответа, если есть ответы
        if total_replies > 0:
            report_lines.extend(
                [
                    f"• <b>{format_seconds(min_time)}</b> и "
                    f"<b>{format_seconds(max_time)}</b> - мин. и макс. время ответов",
                    f"• <b>{format_seconds(avg_time)}</b> и "
                    f"<b>{format_seconds(median_time)}</b> - сред. и медиан. время ответа\n",
                ]
            )
        else:
            report_lines.append("• Нет ответов на сообщения\n")

        # Добавляем информацию о перерывах
        breaks = self._calculate_breaks(sorted_messages)
        if breaks:
            report_lines.append("<b>⏸️ Перерывы:</b>")
            for break_info in breaks:
                report_lines.append(f"• {break_info}")
        else:
            report_lines.append("<b>⏸️ Перерывы:</b> отсутствуют")

        return Report(text="\n".join(report_lines))

    def _messages_per_hour(
        self, messages_count: int, start_date: datetime, end_date: datetime
    ) -> float:
        """Рассчитывает количество сообщений в час."""
        if messages_count < 2:
            return 1
        hours = (end_date - start_date).total_seconds() / 3600
        if hours <= 0:
            return 1
        return round(messages_count / hours, 2)

    def _calculate_breaks(self, messages: list[ChatMessage]) -> list[str]:
        """Считает перерывы между сообщениями."""
        if len(messages) < 2:
            return []

        breaks = []
        for i in range(1, len(messages)):
            # Приводим даты к локальному времени
            prev_msg_time = TimeZoneService.convert_to_local_time(
                messages[i - 1].created_at
            )
            curr_msg_time = TimeZoneService.convert_to_local_time(
                messages[i].created_at
            )

            minutes_diff = (curr_msg_time - prev_msg_time).total_seconds() / 60

            if minutes_diff >= 30:
                start_break = prev_msg_time.strftime("%H:%M")
                end_break = curr_msg_time.strftime("%H:%M")
                date = prev_msg_time.strftime("%d.%m.%Y")
                breaks.append(
                    f"{start_break}-{end_break} — {round(minutes_diff)} мин. ({date})"
                )

        return breaks
