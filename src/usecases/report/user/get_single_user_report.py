import logging
from datetime import datetime
from statistics import mean, median
from typing import List

from constants import MAX_MSG_LENGTH
from dto.report import ResponseTimeReportDTO
from exceptions.user import UserNotFoundException
from models import ChatMessage, MessageReaction, MessageReply, User
from services.break_analysis_service import BreakAnalysisService
from services.work_time_service import WorkTimeService
from utils.formatter import format_seconds

from .base import BaseReportUseCase

logger = logging.getLogger(__name__)


class GetSingleUserReportUseCase(BaseReportUseCase):
    async def execute(self, report_dto: ResponseTimeReportDTO) -> List[str]:
        """Генерирует отчет по выбранному пользователю."""

        user = await self._get_user(user_id=report_dto.user_id)
        user_data = await self._get_user_data(user=user, dto=report_dto)

        full_report = self._generate_report(
            user_data,
            user,
            report_dto.start_date,
            report_dto.end_date,
            report_dto.selected_period,
        )

        return self._split_report(full_report)

    async def _get_user(self, user_id: int) -> User:
        """Получает пользователя по user_id."""
        user = await self._user_repository.get_user_by_id(user_id=user_id)
        if not user:
            logger.error(f"Пользователь с ID={user_id} не найден")
            raise UserNotFoundException()
        return user

    async def _get_user_data(self, user: User, dto: ResponseTimeReportDTO) -> dict:
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
            f"Пользователь {user.username}: {len(messages)} сообщений, "
            f"{len(replies)} ответов, {len(reactions)} реакций"
        )

        return {"replies": replies, "messages": messages, "reactions": reactions}

    def _generate_report(
        self,
        data: dict,
        user: User,
        start_date: datetime,
        end_date: datetime,
        selected_period: str = None,
    ) -> str:
        """Формирует текстовый отчет."""
        period = self._format_selected_period(start_date, end_date)
        replies, messages, reactions = (
            data["replies"],
            data["messages"],
            data["reactions"],
        )

        if not messages and not reactions:
            return "⚠️ Нет данных за указанный период."

        report_parts = [
            f"<b>📈 Отчёт: @{user.username} за {period}</b>\n",
            self._generate_basic_stats(
                messages=messages,
                replies=replies,
                reactions=reactions,
                start_date=start_date,
                end_date=end_date,
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

        # Статистика реакций
        if reactions:
            stats_parts.extend(
                [
                    f"{self.get_time_first_reaction(reactions)}",
                    f"• <b>{len(reactions)}</b> - всего реакций на сообщения\n",
                ]
            )

        # Статистика сообщений
        if messages:
            working_hours = WorkTimeService.calculate_work_hours(start_date, end_date)
            messages_per_hour = self._messages_per_hour(
                len(messages), start_date, end_date
            )

            stats_parts.extend(
                [
                    f"{self.get_time_first_message(messages)}",
                    f"• <b>{working_hours}</b> - кол-во рабочих часов\n",
                    f"• <b>{len(messages)}</b> - всего сообщений",
                    f"• <b>{messages_per_hour}</b> - сообщений в час",
                    f"• Из них <b>{len(replies)}</b> ответ(-ов)",
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
        content_parts = parts[1:]

        result = [title]
        current_part = ""

        for part in content_parts:
            if len(current_part) + len(part) + 2 > MAX_MSG_LENGTH:
                if current_part:
                    result.append(current_part)
                current_part = part
            else:
                current_part = f"{current_part}\n\n{part}" if current_part else part

        if current_part:
            result.append(current_part)

        return result
