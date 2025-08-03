import logging
from datetime import datetime
from statistics import mean, median
from typing import List, Optional

from constants import MAX_MSG_LENGTH
from dto.report import ChatReportDTO
from models import ChatMessage, ChatSession, MessageReaction, MessageReply
from repositories import (
    ChatRepository,
    MessageReactionRepository,
    MessageReplyRepository,
    MessageRepository,
)
from services.break_analysis_service import BreakAnalysisService
from services.time_service import TimeZoneService
from services.work_time_service import WorkTimeService
from utils.formatter import format_seconds, format_selected_period

logger = logging.getLogger(__name__)


class GetReportOnSpecificChatUseCase:
    """UseCase для генерации отчета по конкретному чату."""

    def __init__(
        self,
        msg_reply_repository: MessageReplyRepository,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
        reaction_repository: MessageReactionRepository,
    ):
        self._message_repository = message_repository
        self._msg_reply_repository = msg_reply_repository
        self._chat_repository = chat_repository
        self._reaction_repository = reaction_repository

    async def execute(self, dto: ChatReportDTO) -> List[str]:
        """Генерирует отчет по конкретному чату за указанный период."""
        chat = await self._get_chat(dto.chat_title)
        chat_data = await self._get_chat_data(chat, dto)

        report = self._generate_report(
            chat_data, chat, dto.start_date, dto.end_date, dto.selected_period
        )

        return self._split_report(report)

    async def _get_chat(self, chat_title: str) -> ChatSession:
        """Получает чат по названию."""
        chat = await self._chat_repository.get_chat_by_title(chat_title)
        if not chat:
            raise ValueError("Чат не найден")
        return chat

    async def _get_chat_data(self, chat: ChatSession, dto: ChatReportDTO) -> dict:
        """Получает все данные чата за период."""
        messages = await self._get_processed_items(
            self._message_repository.get_messages_by_chat_id_and_period,
            chat.id,
            dto.start_date,
            dto.end_date,
        )

        replies = await self._get_processed_items(
            self._msg_reply_repository.get_replies_by_chat_id_and_period,
            chat.id,
            dto.start_date,
            dto.end_date,
        )

        reactions = await self._get_processed_items(
            self._reaction_repository.get_reactions_by_chat_and_period,
            chat.id,
            dto.start_date,
            dto.end_date,
        )

        logger.info(
            f"Чат {chat.title}: {len(messages)} сообщений, {len(replies)} ответов, {len(reactions)} реакций"
        )

        return {"messages": messages, "replies": replies, "reactions": reactions}

    async def _get_processed_items(
        self, repository_method, chat_id: int, start_date: datetime, end_date: datetime
    ):
        """Получает и обрабатывает элементы из репозитория."""
        items = await repository_method(
            chat_id=chat_id,
            start_date=start_date,
            end_date=end_date,
        )

        for item in items:
            item.created_at = TimeZoneService.convert_to_local_time(item.created_at)

        return items

    def _generate_report(
        self,
        data: dict,
        chat: ChatSession,
        start_date: datetime,
        end_date: datetime,
        selected_period: Optional[str] = None,
    ) -> str:
        """Формирует текстовый отчет."""
        messages, replies, reactions = (
            data["messages"],
            data["replies"],
            data["reactions"],
        )

        if not messages and not reactions:
            return "⚠️ Нет данных за указанный период."

        period = format_selected_period(selected_period)

        report_parts = [
            f"<b>📈 Отчёт по: {chat.title} за {period}</b>\n",
            self._generate_basic_stats(
                messages, replies, reactions, start_date, end_date
            ),
            self._generate_response_stats(replies),
            self._generate_breaks_section(messages, reactions),
        ]

        return "\n".join(filter(None, report_parts))

    def _generate_basic_stats(
        self,
        messages: List[ChatMessage],
        replies: List[MessageReply],
        reactions: List[MessageReaction],
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Генерирует базовую статистику."""
        stats_parts = []

        # Первые сообщения по дням
        if messages:
            first_messages_info = self._get_first_messages_by_day(messages)
            stats_parts.append(first_messages_info)

        # Статистика активности
        working_hours = WorkTimeService.calculate_work_hours(start_date, end_date)
        total_activity = len(messages) + len(reactions)
        activity_per_hour = self._calculate_activity_per_hour(
            total_activity, working_hours
        )

        stats_parts.extend(
            [
                f"• <b>{len(messages)}</b> - всего сообщений",
                f"• <b>{len(reactions)}</b> - всего реакций",
                f"• <b>{working_hours}</b> - кол-во рабочих часов",
                f"• <b>{activity_per_hour}</b> - активности в час",
                f"• Из них <b>{len(replies)}</b> ответ(-ов)\n",
            ]
        )

        return "\n".join(stats_parts)

    def _generate_response_stats(self, replies: List[MessageReply]) -> str:
        """Генерирует статистику времени ответа."""
        if not replies:
            return "• <b>Нет ответов</b> за указанный период\n"

        response_times = [reply.response_time_seconds for reply in replies]
        stats = {
            "avg": mean(response_times),
            "median": median(response_times),
            "min": min(response_times),
            "max": max(response_times),
        }

        return "\n".join(
            [
                f"• <b>{format_seconds(stats['min'])}</b> и <b>{format_seconds(stats['max'])}</b> - мин. и макс. время ответов",
                f"• <b>{format_seconds(stats['avg'])}</b> и <b>{format_seconds(stats['median'])}</b> - сред. и медиан. время ответа\n",
            ]
        )

    def _generate_breaks_section(
        self, messages: List[ChatMessage], reactions: List[MessageReaction]
    ) -> str:
        """Генерирует секцию с перерывами."""
        if not messages and not reactions:
            return "<b>⏸️ Перерывы:</b> отсутствуют"

        sorted_messages = sorted(messages, key=lambda m: m.created_at)
        breaks = BreakAnalysisService.calculate_breaks(sorted_messages, reactions)

        if breaks:
            return "<b>⏸️ Перерывы:</b>\n" + "\n".join(breaks)
        return "<b>⏸️ Перерывы:</b> отсутствуют"

    def _get_first_messages_by_day(self, messages: List[ChatMessage]) -> str:
        """Возвращает список времени первого сообщения в день."""
        if not messages:
            return ""

        sorted_messages = sorted(messages, key=lambda m: m.created_at)
        first_messages_by_day = {}

        for message in sorted_messages:
            date = message.created_at.date()
            if date not in first_messages_by_day:
                first_messages_by_day[date] = message

        result = []
        for date, message in sorted(first_messages_by_day.items()):
            result.append(
                f"• {message.created_at.strftime('%H:%M')} - первое сообщение "
                f"{message.created_at.strftime('%d.%m.%Y')}"
            )

        return "\n".join(result) + "\n"

    def _calculate_activity_per_hour(
        self, activity_count: int, work_hours: float
    ) -> float:
        """Рассчитывает количество активности в час рабочего времени."""
        if activity_count < 1 or work_hours <= 0:
            return 0.0
        return round(activity_count / work_hours, 2)

    def _split_report(self, report: str) -> List[str]:
        """Разделяет отчет на части по лимиту длины."""
        if len(report) <= MAX_MSG_LENGTH:
            return [report]

        parts = report.split("<b>⏸️ Перерывы:</b>")
        main_part = parts[0]
        breaks_part = parts[1] if len(parts) > 1 else ""

        result = [main_part + "Перерывы: см. следующее сообщение"]

        if breaks_part:
            breaks_lines = breaks_part.split("\n")
            current_part = "<b>⏸️ Перерывы:</b>"

            for line in breaks_lines:
                if len(current_part) + len(line) + 1 > MAX_MSG_LENGTH:
                    result.append(current_part)
                    current_part = "<b>⏸️ Перерывы (продолжение):</b>"
                current_part += "\n" + line

            if current_part:
                result.append(current_part)

        return result
