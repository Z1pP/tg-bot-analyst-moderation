import logging
from datetime import datetime
from statistics import mean, median
from typing import List

from constants import MAX_MSG_LENGTH
from dto.report import AllModeratorReportDTO
from models import ChatMessage, MessageReaction, MessageReply, User
from services.break_analysis_service import BreakAnalysisService
from utils.formatter import format_seconds

from .base import BaseReportUseCase

logger = logging.getLogger(__name__)


class GetAllModeratorsReportUseCase(BaseReportUseCase):
    async def execute(self, dto: AllModeratorReportDTO) -> List[str]:
        """Генерирует отчет по всем модераторам за указанный период."""
        users = await self._user_repository.get_all_moderators()

        if not users:
            logger.error(f"Количество найденных модераторов = {len(users)}")
            return ["⚠️ Список модераторов пуст, добавьте модератора!"]

        selected_period = self._format_selected_period(dto.selected_period)
        report_title = f"<b>📈 Отчет по модераторам за {selected_period}</b>"

        reports = []
        for user in users:
            user_data = await self._get_user_data(user, dto)
            if not user_data["messages"] and not user_data["reactions"]:
                continue

            report = self._generate_user_report(
                user_data, user, dto.start_date, dto.end_date
            )
            reports.append(report)

        full_report = "\n\n".join([report_title] + reports)
        return self._split_report(full_report)

    async def _get_user_data(self, user: User, dto: AllModeratorReportDTO) -> dict:
        """Получает все данные пользователя за период."""
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

        reactions = await self._get_processed_items(
            self._reaction_repository.get_reactions_by_user_and_period,
            user.id,
            dto.start_date,
            dto.end_date,
        )

        logger.info(
            f"Пользователь {user.username}: {len(messages)} сообщений, {len(replies)} ответов, {len(reactions)} реакций"
        )

        return {"replies": replies, "messages": messages, "reactions": reactions}

    def _generate_user_report(
        self, data: dict, user: User, start_date: datetime, end_date: datetime
    ) -> str:
        """Создает отчет для одного пользователя."""
        replies, messages, reactions = (
            data["replies"],
            data["messages"],
            data["reactions"],
        )

        if not messages and not reactions:
            return f"<b>👤 @{user.username}</b>\nНет активности за указанный период"

        report_parts = [f"<b>👤 @{user.username}</b>\n"]

        # Статистика реакций
        if reactions:
            report_parts.extend(
                [
                    f"{self.get_time_first_reaction(reactions)}",
                    f"• <b>{len(reactions)}</b> - всего реакций на сообщения\n",
                ]
            )

        # Статистика сообщений
        if messages:
            avg_per_hour = self._messages_per_hour(len(messages), start_date, end_date)
            report_parts.extend(
                [
                    f"{self.get_time_first_message(messages)}",
                    f"• <b>{len(messages)}</b> - всего сообщений",
                    f"• <b>{avg_per_hour:.2f}</b> - сред. кол-во сообщ. в час\n",
                ]
            )

        # Статистика ответов
        if replies:
            response_stats = self._calculate_response_stats(replies)
            report_parts.append(f"• Из них <b>{len(replies)}</b> ответ(-ов)")
            report_parts.extend(response_stats)
        else:
            report_parts.append("• <b>Нет ответов</b> за указанный период")

        # Перерывы
        report_parts.extend(["", self._generate_breaks_section(messages, reactions)])

        return "\n".join(report_parts)

    def _calculate_response_stats(self, replies: List[MessageReply]) -> List[str]:
        """Вычисляет статистику времени ответа."""
        response_times = [reply.response_time_seconds for reply in replies]
        if not response_times:
            return []

        stats = {
            "avg": round(mean(response_times), 2),
            "median": round(median(response_times), 2),
            "min": round(min(response_times), 2),
            "max": round(max(response_times), 2),
        }

        return [
            f"• <b>{format_seconds(stats['min'])}</b> и <b>{format_seconds(stats['max'])}</b> - мин. и макс. время ответа",
            f"• <b>{format_seconds(stats['avg'])}</b> и <b>{format_seconds(stats['median'])}</b> - сред. и медиан. время ответа",
        ]

    def _generate_breaks_section(
        self, messages: List[ChatMessage], reactions: List[MessageReaction]
    ) -> str:
        """Генерирует секцию с перерывами."""
        sorted_messages = sorted(messages, key=lambda m: m.created_at)
        breaks = BreakAnalysisService.calculate_breaks(sorted_messages, reactions)

        if breaks:
            return "<b>⏸️ Перерывы:</b>\n" + "\n".join(breaks)
        return "<b>⏸️ Перерывы:</b> отсутствуют"

    def _split_report(self, report: str) -> List[str]:
        """Разделяет отчет на части по лимиту длины."""
        if len(report) <= MAX_MSG_LENGTH:
            return [report]

        parts = report.split("\n\n")
        title = parts[0]
        user_reports = parts[1:]

        result = [title]
        current_part = ""

        for user_report in user_reports:
            if len(current_part) + len(user_report) + 2 > MAX_MSG_LENGTH:
                if current_part:
                    result.append(current_part)
                current_part = user_report
            else:
                current_part = (
                    f"{current_part}\n\n{user_report}" if current_part else user_report
                )

        if current_part:
            result.append(current_part)

        return result
