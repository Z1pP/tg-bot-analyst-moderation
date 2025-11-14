import logging
from datetime import datetime
from statistics import mean, median
from typing import List

from constants import MAX_MSG_LENGTH
from constants.enums import AdminActionType
from dto.report import AllUsersReportDTO
from models import ChatMessage, MessageReaction, MessageReply, User
from repositories import (
    ChatRepository,
    MessageReactionRepository,
    MessageReplyRepository,
    MessageRepository,
    UserRepository,
)
from services import AdminActionLogService
from services.break_analysis_service import BreakAnalysisService
from utils.formatter import format_seconds

from .base import BaseReportUseCase

logger = logging.getLogger(__name__)


class GetAllUsersReportUseCase(BaseReportUseCase):
    def __init__(
        self,
        msg_reply_repository: MessageReplyRepository,
        message_repository: MessageRepository,
        user_repository: UserRepository,
        reaction_repository: MessageReactionRepository,
        chat_repository: ChatRepository,
        admin_action_log_service: AdminActionLogService = None,
    ):
        super().__init__(
            msg_reply_repository,
            message_repository,
            user_repository,
            reaction_repository,
            chat_repository,
        )
        self._admin_action_log_service = admin_action_log_service

    async def execute(self, dto: AllUsersReportDTO) -> List[str]:
        """Генерирует отчет по всем пользователям за выбранным период."""
        users = await self._user_repository.get_tracked_users_for_admin(
            admin_tg_id=dto.user_tg_id,
        )

        if not users:
            logger.error(f"Количество пользователей = {len(users)}")
            return ["⚠️ Список пользователей пуст, добавьте пользователя!"]

        # Определяем тип отчета
        is_single_day = self._is_single_day_report(
            selected_period=dto.selected_period,
            start_date=dto.start_date,
            end_date=dto.end_date,
        )

        period = self._format_selected_period(
            start_date=dto.start_date,
            end_date=dto.end_date,
        )
        period_text = "период " if not is_single_day else ""
        report_title = f"<b>📈 Отчет по пользователям за {period_text}{period}</b>"

        reports = []
        for user in users:
            user_data = await self._get_user_data(user, dto)
            if not user_data["messages"] and not user_data["reactions"]:
                continue

            report = self._generate_unified_user_report(
                user_data, user, dto.start_date, dto.end_date, is_single_day
            )
            reports.append(report)

        full_report = "\n\n".join([report_title] + reports)
        report_parts = self._split_report(full_report)

        # Логируем действие после успешной генерации отчета
        if self._admin_action_log_service:
            period = self._format_selected_period(dto.start_date, dto.end_date)
            details = f"Период: {period}"
            await self._admin_action_log_service.log_action(
                admin_tg_id=dto.user_tg_id,
                action_type=AdminActionType.REPORT_ALL_USERS,
                details=details,
            )

        return report_parts

    async def _get_user_data(self, user: User, dto: AllUsersReportDTO) -> dict:
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

    def _generate_unified_user_report(
        self,
        data: dict,
        user: User,
        start_date: datetime,
        end_date: datetime,
        is_single_day: bool,
    ) -> str:
        """Универсальный генератор отчетов для одного пользователя."""
        replies = data.get("replies", [])
        messages = data.get("messages", [])
        reactions = data.get("reactions", [])

        if not messages and not reactions:
            no_data_text = "день" if is_single_day else "период"
            return (
                f"<b>👤 @{user.username}</b>\n⚠️ Нет данных за указанный {no_data_text}."
            )

        report_parts = [f"<b>👤 @{user.username}</b>\n"]

        # Выбираем методы в зависимости от типа отчета
        stats_method = (
            self._generate_messages_and_reactions_stats
            if is_single_day
            else self._generate_avg_messages_and_reactions_stats
        )
        breaks_method = (
            self._generate_breaks_section
            if is_single_day
            else self._generate_breaks_multiday_section
        )

        report_parts.extend(
            [
                stats_method(messages, reactions, start_date, end_date),
                self._generate_replies_stats(replies),
                breaks_method(messages, reactions),
            ]
        )

        return "\n".join(filter(None, report_parts))

    def _generate_avg_messages_and_reactions_stats(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Генерирует средние значения по сообщениям и реакциям"""
        msg_count = len(messages)
        return "\n".join(
            [
                f"• <b>{self.get_avg_time_first_messages(messages)}</b> - среднее время отправки 1-х сообщений",
                f"• <b>{self.get_avg_time_first_reaction(reactions)}</b> - среднее время 1-й реакции на сообщение",
                "",
                f"• <b>{self._avg_messages_per_hour(msg_count, start_date, end_date)}</b> - сред. кол-во сообщ./час",
                f"• <b>{self._avg_message_per_day(msg_count, start_date, end_date)}</b> - сред. кол-во сообщ./день",
                f"• <b>{msg_count}</b> - всего сообщ. за период",
            ]
        )

    def _generate_messages_and_reactions_stats(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Генерирует статистику по сообщениям и реакциям"""
        msg_count = len(messages)
        return "\n".join(
            [
                f"• <b>{self.get_time_first_message(messages)}</b> - 1-е сообщение",
                f"• <b>{self.get_time_first_reaction(reactions)}</b> - 1-я реакция на сообщение",
                "",
                f"• <b>{self._avg_messages_per_hour(msg_count, start_date, end_date)}</b> - сред. кол-во сообщ./час",
                f"• <b>{msg_count}</b> - всего сообщений",
            ]
        )

    def _generate_replies_stats(self, replies: List[MessageReply]) -> str:
        """Генерирует статистику по времени ответа"""
        if not replies:
            return "• <b>Нет ответов</b> за указанный период"

        times = [reply.response_time_seconds for reply in replies]
        return "\n".join(
            [
                f"Из них <b>{len(replies)}</b> ответов:",
                f"• <b>{format_seconds(min(times))}</b> - мин. время ответа",
                f"• <b>{format_seconds(max(times))}</b> - макс. время ответа",
                f"• <b>{format_seconds(int(mean(times)))}</b> - сред. время ответа",
                f"• <b>{format_seconds(int(median(times)))}</b> - медиан. время ответа",
                "",
            ]
        )

    def _generate_breaks_multiday_section(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
    ) -> str:
        avg_breaks_time = BreakAnalysisService.avg_breaks_time(messages, reactions)
        if avg_breaks_time:
            breaks_text = (
                "<b>⏸️ Перерывы:</b>\n"
                f"• <b>{avg_breaks_time}</b> - средн. время перерыва между сообщ. и реакциями"
            )
        else:
            breaks_text = "<b>⏸️ Перерывы:</b> отсутствуют"

        return breaks_text

    def is_single_day_report(self, report_dto: AllUsersReportDTO) -> bool:
        """Проверяет, является ли отчет однодневным."""
        return self._is_single_day_report(
            selected_period=report_dto.selected_period,
            start_date=report_dto.start_date,
            end_date=report_dto.end_date,
        )

    def _is_single_day_report(
        self,
        selected_period: str,
        start_date: datetime,
        end_date: datetime,
    ) -> bool:
        """Определяет, является ли отчет за один день."""
        from constants.period import TimePeriod

        if selected_period:
            return selected_period in [
                TimePeriod.TODAY.value,
                TimePeriod.YESTERDAY.value,
            ]

        return (end_date.date() - start_date.date()).days <= 1

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
