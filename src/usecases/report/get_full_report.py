from datetime import datetime
from statistics import mean, median
from typing import Awaitable, Callable

from dto.report import AllModeratorReportDTO
from models import ChatMessage, MessageReply, User
from repositories import (
    MessageReplyRepository,
    MessageRepository,
    UserRepository,
)
from services.time_service import TimeZoneService
from services.work_time_service import WorkTimeService


class GetAllModeratorsReportUseCase:
    def __init__(
        self,
        msg_reply_repository: MessageReplyRepository,
        message_repository: MessageRepository,
        user_repository: UserRepository,
    ):
        self._msg_reply_repository = msg_reply_repository
        self._user_repository = user_repository
        self._message_repository = message_repository

    async def execute(self, dto: AllModeratorReportDTO) -> str:
        users = await self._user_repository.get_all_users()

        if not users:
            return "⚠️ Не выбран не один модератор!"

        # Конвертируем дату согласно UTC +3
        dto.start_date = TimeZoneService.convert_to_local_time(dto.start_date)
        dto.end_date = TimeZoneService.convert_to_local_time(dto.end_date)

        selected_period = self._format_selected_period(dto.selected_period)
        report_title = f"Отчет по модераторам за {selected_period}"
        report_period = f"Период: {dto.start_date.strftime('%d.%m.%Y')} - {dto.end_date.strftime('%d.%m.%Y')}"

        reports = []
        for user in users:
            # Получаем и обрабатываем данные для отчета
            replies = await self._get_processed_items(
                self._msg_reply_repository.get_replies_by_period_date,
                user.id,
                dto.start_date,
                dto.end_date,
            )

            messages = await self._get_processed_items(
                self._message_repository.get_messages_by_period_date,
                user.id,
                dto.start_date,
                dto.end_date,
            )

            if not messages:
                continue

            report = self._generate_report(
                replies=replies,
                messages=messages,
                user=user,
                start_date=dto.start_date,
                end_date=dto.end_date,
            )
            reports.append(report)

        return "\n\n".join([report_title] + [report_period] + reports)

    async def _get_processed_items(
        self,
        repository_method: Callable[[int, datetime, datetime], Awaitable[list]],
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ):
        """Получает и обрабатывает элементы из репозитория"""
        items = await repository_method(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        for item in items:
            item.created_at = TimeZoneService.convert_to_local_time(item.created_at)

        return WorkTimeService.filter_by_work_time(items=items)

    def _generate_report(
        self,
        replies: list[MessageReply],
        messages: list[ChatMessage],
        user: User,
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Создает отчет для одного модератора"""
        sorted_messages = sorted(messages, key=lambda r: r.created_at)

        response_times = (
            [reply.response_time_seconds for reply in replies] if replies else [0]
        )
        total_message = len(messages)
        total_replies = len(replies)

        period_hours = (end_date - start_date).total_seconds() / 3600
        avg_message_per_hour = (
            round(total_message / period_hours, 2) if period_hours else 0
        )

        # Рассчитываем статистику
        avg_time = round(mean(response_times), 2)
        median_time = round(median(response_times), 2)
        min_time = round(min(response_times), 2)
        max_time = round(max(response_times), 2)

        breaks = self._calculate_breaks(sorted_messages)

        report = [
            f"@{user.username}",
            f"Всего сообщений: <b>{total_message}</b>",
            f"Сред. кол-во сообщ. в час: <b>{avg_message_per_hour:.2f}</b>",
            f"Всего ответов: <b>{total_replies}</b>",
            f"Мин. и макс. время ответа: <b>{min_time} сек.</b> и <b>{max_time / 60:.2f} мин.</b>",
            f"Сред. и медиан. время ответа: <b>{avg_time} сек.</b> и <b>{median_time} сек.</b>",
        ]

        if breaks:
            report.append("Перерывы:")
            report.extend(f"- {break_info}" for break_info in breaks)
        else:
            report.append("Перерывы: отсутствуют")

        return "\n".join(report)

    def _format_selected_period(self, selected_period: str) -> str:
        """Форматирует выбранный период в читаемый формат"""
        if not selected_period:
            return "<b>указанный период</b>"
        return selected_period.split("За")[-1].strip()

    def _calculate_breaks(self, messages: list[ChatMessage]) -> list[str]:
        """Считает перерывы между сообщениями"""
        if len(messages) < 2:
            return []

        breaks = []
        for i in range(1, len(messages)):
            prev_msg, curr_msg = messages[i - 1], messages[i]

            minutes_diff = (
                curr_msg.created_at - prev_msg.created_at
            ).total_seconds() / 60

            if minutes_diff >= 30:
                start_break = prev_msg.created_at.strftime("%H:%M")
                end_break = curr_msg.created_at.strftime("%H:%M")
                date = prev_msg.created_at.strftime("%d.%m.%Y")
                breaks.append(
                    f"{start_break}-{end_break} — {round(minutes_diff)} мин. ({date})"
                )

        return breaks
