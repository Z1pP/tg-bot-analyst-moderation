import logging
from datetime import datetime
from statistics import mean, median
from typing import List

from constants.enums import AdminActionType
from dto.report import SingleUserReportDTO
from exceptions.user import UserNotFoundException
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


class GetSingleUserReportUseCase(BaseReportUseCase):
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

    async def execute(self, report_dto: SingleUserReportDTO) -> List[str]:
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

        report_parts = self._split_report(full_report)

        # Логируем действие после успешной генерации отчета
        if self._admin_action_log_service:
            period = self._format_selected_period(
                report_dto.start_date, report_dto.end_date
            )
            details = f"Пользователь: @{user.username}, Период: {period}"
            await self._admin_action_log_service.log_action(
                admin_tg_id=report_dto.admin_tg_id,
                action_type=AdminActionType.REPORT_USER,
                details=details,
            )

        return report_parts

    def is_single_day_report(self, report_dto: SingleUserReportDTO) -> bool:
        """Проверяет, является ли отчет однодневным."""
        return self._is_single_day_report(
            selected_period=report_dto.selected_period,
            start_date=report_dto.start_date,
            end_date=report_dto.end_date,
        )

    async def _get_user(self, user_id: int) -> User:
        """Получает пользователя по user_id."""
        user = await self._user_repository.get_user_by_id(user_id=user_id)
        if not user:
            logger.error(f"Пользователь с ID={user_id} не найден")
            raise UserNotFoundException()
        return user

    async def _get_user_data(self, user: User, dto: SingleUserReportDTO) -> dict:
        """Получает все данные пользователя за период."""
        # Проверяем наличие отслеживаемых чатов
        tracked_chats = await self._chat_repository.get_tracked_chats_for_admin(
            dto.admin_tg_id
        )
        if not tracked_chats:
            return {"no_chats": True}

        tracked_chat_ids = [chat.id for chat in tracked_chats]

        replies = await self._get_processed_items_by_user_in_chats(
            repository_method=self._msg_reply_repository.get_replies_by_period_date_and_chats,
            user_id=user.id,
            start_date=dto.start_date,
            end_date=dto.end_date,
            chat_ids=tracked_chat_ids,
        )

        messages = await self._get_processed_items_by_user_in_chats(
            repository_method=self._message_repository.get_messages_by_period_date_and_chats,
            user_id=user.id,
            start_date=dto.start_date,
            end_date=dto.end_date,
            chat_ids=tracked_chat_ids,
        )

        reactions = await self._get_processed_items_by_user_in_chats(
            repository_method=self._reaction_repository.get_reactions_by_user_and_period_and_chats,
            user_id=user.id,
            start_date=dto.start_date,
            end_date=dto.end_date,
            chat_ids=tracked_chat_ids,
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

        # Проверяем наличие отслеживаемых чатов
        if data.get("no_chats"):
            period = self._format_selected_period(start_date, end_date)
            return (
                f"<b>📈 Отчёт: @{user.username} за {period}</b>\n\n"
                "⚠️ Необходимо добавить чат в отслеживание."
            )

        replies = data.get("replies", [])
        messages = data.get("messages", [])
        reactions = data.get("reactions", [])

        # Определяем тип отчета по периоду
        is_single_day = self._is_single_day_report(
            selected_period=selected_period,
            start_date=start_date,
            end_date=end_date,
        )

        if is_single_day:
            return self._generate_single_day_report(
                user=user,
                messages=messages,
                replies=replies,
                reactions=reactions,
                start_date=start_date,
                end_date=end_date,
            )
        else:
            return self._generate_multi_day_report(
                user=user,
                messages=messages,
                replies=replies,
                reactions=reactions,
                start_date=start_date,
                end_date=end_date,
            )

    def _generate_single_day_report(
        self,
        user: User,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        replies: List[MessageReply],
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Генрирует отчет для одного дня"""
        return self._generate_unified_report(
            user, messages, reactions, replies, start_date, end_date, is_single_day=True
        )

    def _generate_multi_day_report(
        self,
        user: User,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        replies: List[MessageReply],
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Генрирует отчет за указанный период дней"""
        return self._generate_unified_report(
            user,
            messages,
            reactions,
            replies,
            start_date,
            end_date,
            is_single_day=False,
        )

    def _generate_unified_report(
        self,
        user: User,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        replies: List[MessageReply],
        start_date: datetime,
        end_date: datetime,
        is_single_day: bool,
    ) -> str:
        """Универсальный генератор отчетов"""
        period = self._format_selected_period(start_date, end_date)
        period_text = "период " if not is_single_day else ""

        report_parts = [f"<b>📈 Отчёт: @{user.username} за {period_text}{period}</b>\n"]

        if not messages and not reactions:
            no_data_text = "день" if is_single_day else "период"
            report_parts.append(f"⚠️ Нет данных за указанный {no_data_text}.")
            return "\n".join(report_parts)

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
                breaks_method(messages, reactions, is_single_day),
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
        is_single_day: bool = False,
    ) -> str:
        avg_breaks_time = BreakAnalysisService.avg_breaks_time(messages, reactions)
        if avg_breaks_time:
            breaks_text = (
                "<b>⏸️ Перерывы:</b>\n"
                f"• <b>{avg_breaks_time}</b> - средн. время перерыва между сообщ. и реакциями"
            )
        else:
            breaks_text = "<b>⏸️ Перерывы:</b> отсутствуют"

        return breaks_text + (
            "\n\n❗Чтобы получить детализацию перерывов по датам, нажмите "
            "соответствующую кнопку"
        )

    def _generate_breaks_section(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        is_single_day: bool = False,
    ) -> str:
        """Генерирует секцию с перерывами."""
        breaks = BreakAnalysisService.calculate_breaks(
            messages,
            reactions,
            is_single_day=is_single_day,
        )
        return (
            "<b>⏸️ Перерывы:</b>\n" + "\n".join(breaks)
            if breaks
            else "<b>⏸️ Перерывы:</b> отсутствуют"
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
