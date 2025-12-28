import logging
from datetime import datetime
from statistics import mean, median
from typing import List, Optional

from constants.enums import AdminActionType
from constants.period import TimePeriod
from constants.work_time import END_TIME, START_TIME, TOLERANCE
from dto.report import (
    RepliesStats,
    SingleUserDayStats,
    SingleUserMultiDayStats,
    SingleUserReportDTO,
    SingleUserReportResultDTO,
)
from exceptions.user import UserNotFoundException
from models import ChatMessage, MessageReaction, MessageReply, User
from repositories import (
    ChatRepository,
    MessageReactionRepository,
    MessageReplyRepository,
    MessageRepository,
    PunishmentRepository,
    UserRepository,
)
from services import AdminActionLogService
from services.break_analysis_service import BreakAnalysisService
from services.work_time_service import WorkTimeService

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
        punishment_repository: PunishmentRepository,
        admin_action_log_service: AdminActionLogService = None,
    ):
        super().__init__(
            msg_reply_repository,
            message_repository,
            user_repository,
            reaction_repository,
            chat_repository,
            punishment_repository,
        )
        self._admin_action_log_service = admin_action_log_service

    async def execute(
        self, report_dto: SingleUserReportDTO
    ) -> SingleUserReportResultDTO:
        """Генерирует отчет по выбранному пользователю."""

        # Корректируем даты в соответствии с рабочими часами
        adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
            start_date=report_dto.start_date,
            end_date=report_dto.end_date,
            work_start=START_TIME,
            work_end=END_TIME,
            tolerance=TOLERANCE,
        )

        user = await self._get_user(user_id=report_dto.user_id)

        # Определяем тип отчета
        is_single_day = self._is_single_day_report(
            selected_period=report_dto.selected_period,
            start_date=adjusted_start,
            end_date=adjusted_end,
        )

        # Получаем данные пользователя
        user_data = await self._get_user_data(
            user=user, dto=report_dto, start_date=adjusted_start, end_date=adjusted_end
        )

        # Проверяем наличие отслеживаемых чатов
        if user_data.get("no_chats"):
            return SingleUserReportResultDTO(
                username=user.username,
                user_id=user.id,
                start_date=adjusted_start,
                end_date=adjusted_end,
                is_single_day=is_single_day,
                day_stats=None,
                multi_day_stats=None,
                replies_stats=RepliesStats(
                    total_count=0,
                    min_time_seconds=None,
                    max_time_seconds=None,
                    avg_time_seconds=None,
                    median_time_seconds=None,
                ),
                breaks=[],
                error_message="⚠️ Необходимо добавить чат в отслеживание.",
            )

        replies = user_data.get("replies", [])
        messages = user_data.get("messages", [])
        reactions = user_data.get("reactions", [])

        # Получаем статистику наказаний, выданных пользователем
        punishment_stats = (
            await self._punishment_repository.get_punishment_counts_by_moderator(
                moderator_id=user.id,
                start_date=adjusted_start,
                end_date=adjusted_end,
            )
        )

        # Рассчитываем статистику
        if is_single_day:
            day_stats = self._calculate_day_stats(
                messages,
                reactions,
                adjusted_start,
                adjusted_end,
                warns_count=punishment_stats["warns"],
                bans_count=punishment_stats["bans"],
            )
            multi_day_stats = None
        else:
            day_stats = None
            multi_day_stats = self._calculate_multi_day_stats(
                messages,
                reactions,
                adjusted_start,
                adjusted_end,
                warns_count=punishment_stats["warns"],
                bans_count=punishment_stats["bans"],
            )

        replies_stats = self._calculate_replies_stats(replies)
        breaks = self._calculate_breaks(messages, reactions, is_single_day)

        # Логируем действие после успешной генерации отчета
        if self._admin_action_log_service:
            period = self._format_selected_period(adjusted_start, adjusted_end)
            details = f"Пользователь: @{user.username}, Период: {period}"
            await self._admin_action_log_service.log_action(
                admin_tg_id=report_dto.admin_tg_id,
                action_type=AdminActionType.REPORT_USER,
                details=details,
            )

        return SingleUserReportResultDTO(
            username=user.username,
            user_id=user.id,
            start_date=adjusted_start,
            end_date=adjusted_end,
            is_single_day=is_single_day,
            day_stats=day_stats,
            multi_day_stats=multi_day_stats,
            replies_stats=replies_stats,
            breaks=breaks,
        )

    async def _get_user(self, user_id: int) -> User:
        """Получает пользователя по user_id."""
        user = await self._user_repository.get_user_by_id(user_id=user_id)
        if not user:
            logger.error(f"Пользователь с ID={user_id} не найден")
            raise UserNotFoundException()
        return user

    async def _get_user_data(
        self,
        user: User,
        dto: SingleUserReportDTO,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
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
            start_date=start_date,
            end_date=end_date,
            chat_ids=tracked_chat_ids,
        )

        messages = await self._get_processed_items_by_user_in_chats(
            repository_method=self._message_repository.get_messages_by_period_date_and_chats,
            user_id=user.id,
            start_date=start_date,
            end_date=end_date,
            chat_ids=tracked_chat_ids,
        )

        reactions = await self._get_processed_items_by_user_in_chats(
            repository_method=self._reaction_repository.get_reactions_by_user_and_period_and_chats,
            user_id=user.id,
            start_date=start_date,
            end_date=end_date,
            chat_ids=tracked_chat_ids,
        )

        logger.info(
            f"Пользователь {user.username}: {len(messages)} сообщений, "
            f"{len(replies)} ответов, {len(reactions)} реакций"
        )

        return {"replies": replies, "messages": messages, "reactions": reactions}

    def _calculate_day_stats(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        start_date: datetime,
        end_date: datetime,
        warns_count: int = 0,
        bans_count: int = 0,
    ) -> Optional[SingleUserDayStats]:
        """Рассчитывает статистику за один день."""

        if not messages and not reactions and warns_count == 0 and bans_count == 0:
            return None

        first_message_time = None
        if messages:
            first_message = min(messages, key=lambda m: m.created_at)
            first_message_time = first_message.created_at

        first_reaction_time = None
        if reactions:
            first_reaction = min(reactions, key=lambda r: r.created_at)
            first_reaction_time = first_reaction.created_at

        msg_count = len(messages)
        avg_messages_per_hour = self._avg_messages_per_hour(
            msg_count, start_date, end_date
        )

        return SingleUserDayStats(
            first_message_time=first_message_time,
            first_reaction_time=first_reaction_time,
            avg_messages_per_hour=avg_messages_per_hour,
            total_messages=msg_count,
            warns_count=warns_count,
            bans_count=bans_count,
        )

    def _calculate_multi_day_stats(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        start_date: datetime,
        end_date: datetime,
        warns_count: int = 0,
        bans_count: int = 0,
    ) -> Optional[SingleUserMultiDayStats]:
        """Рассчитывает статистику за несколько дней."""
        if not messages and not reactions and warns_count == 0 and bans_count == 0:
            return None

        avg_first_message_time = self.get_avg_time_first_messages(messages)
        avg_first_reaction_time = self.get_avg_time_first_reaction(reactions)

        msg_count = len(messages)
        avg_messages_per_hour = self._avg_messages_per_hour(
            msg_count, start_date, end_date
        )
        avg_messages_per_day = self._avg_message_per_day(
            msg_count, start_date, end_date
        )

        return SingleUserMultiDayStats(
            avg_first_message_time=avg_first_message_time or None,
            avg_first_reaction_time=avg_first_reaction_time or None,
            avg_messages_per_hour=avg_messages_per_hour,
            avg_messages_per_day=avg_messages_per_day,
            total_messages=msg_count,
            warns_count=warns_count,
            bans_count=bans_count,
        )

    def _calculate_replies_stats(self, replies: List[MessageReply]) -> RepliesStats:
        """Рассчитывает статистику по ответам."""
        if not replies:
            return RepliesStats(
                total_count=0,
                min_time_seconds=None,
                max_time_seconds=None,
                avg_time_seconds=None,
                median_time_seconds=None,
            )

        times = [reply.response_time_seconds for reply in replies]
        return RepliesStats(
            total_count=len(replies),
            min_time_seconds=int(min(times)),
            max_time_seconds=int(max(times)),
            avg_time_seconds=int(mean(times)),
            median_time_seconds=int(median(times)),
        )

    def _calculate_breaks(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        is_single_day: bool,
    ) -> List[str]:
        """Рассчитывает перерывы."""
        if is_single_day:
            breaks = BreakAnalysisService.calculate_breaks(
                messages, reactions, is_single_day=True
            )
            return breaks
        else:
            avg_breaks_time = BreakAnalysisService.avg_breaks_time(messages, reactions)
            if avg_breaks_time:
                return [
                    f"• <b>{avg_breaks_time}</b> - средн. время перерыва между сообщ. и реакциями"
                ]
            return []

    def _is_single_day_report(
        self,
        selected_period: Optional[str],
        start_date: datetime,
        end_date: datetime,
    ) -> bool:
        """Определяет, является ли отчет за один день."""
        if selected_period:
            return selected_period in [
                TimePeriod.TODAY.value,
                TimePeriod.YESTERDAY.value,
            ]

        return (end_date.date() - start_date.date()).days <= 1
