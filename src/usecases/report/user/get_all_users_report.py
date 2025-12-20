import logging
from datetime import datetime
from statistics import mean, median
from typing import List, Optional

from constants.enums import AdminActionType
from constants.period import TimePeriod
from constants.work_time import END_TIME, START_TIME, TOLERANCE
from dto.report import (
    AllUsersReportDTO,
    AllUsersReportResultDTO,
    AllUsersUserStatsResult,
    RepliesStats,
    SingleUserDayStats,
    SingleUserMultiDayStats,
)
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
from services.work_time_service import WorkTimeService

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

    async def execute(self, dto: AllUsersReportDTO) -> AllUsersReportResultDTO:
        """Генерирует отчет по всем пользователям за выбранным период."""

        # Корректируем даты в соответствии с рабочими часами
        adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
            start_date=dto.start_date,
            end_date=dto.end_date,
            work_start=START_TIME,
            work_end=END_TIME,
            tolerance=TOLERANCE,
        )

        # Определяем тип отчета
        is_single_day = self._is_single_day_report(
            selected_period=dto.selected_period,
            start_date=adjusted_start,
            end_date=adjusted_end,
        )

        users = await self._user_repository.get_tracked_users_for_admin(
            admin_tg_id=dto.user_tg_id,
        )

        if not users:
            logger.error(f"Количество пользователей = {len(users)}")
            return AllUsersReportResultDTO(
                start_date=adjusted_start,
                end_date=adjusted_end,
                is_single_day=is_single_day,
                users_stats=[],
                error_message="⚠️ Список пользователей пуст, добавьте пользователя!",
            )

        # TODO: Оптимизация N+1 проблемы
        # В текущей реализации для каждого пользователя делаются отдельные запросы:
        # - get_replies_by_period_date
        # - get_messages_by_period_date
        # - get_reactions_by_user_and_period
        # Необходимо оптимизировать через batch-запросы для всех пользователей сразу
        users_stats = []
        for user in users:
            user_data = await self._get_user_data(user, adjusted_start, adjusted_end)
            if not user_data["messages"] and not user_data["reactions"]:
                continue

            user_stats = self._calculate_user_stats(
                user=user,
                messages=user_data["messages"],
                reactions=user_data["reactions"],
                replies=user_data["replies"],
                start_date=adjusted_start,
                end_date=adjusted_end,
                is_single_day=is_single_day,
            )
            users_stats.append(user_stats)

        # Логируем действие после успешной генерации отчета
        if self._admin_action_log_service:
            period = self._format_selected_period(adjusted_start, adjusted_end)
            details = f"Период: {period}"
            await self._admin_action_log_service.log_action(
                admin_tg_id=dto.user_tg_id,
                action_type=AdminActionType.REPORT_ALL_USERS,
                details=details,
            )

        return AllUsersReportResultDTO(
            start_date=adjusted_start,
            end_date=adjusted_end,
            is_single_day=is_single_day,
            users_stats=users_stats,
        )

    async def _get_user_data(
        self, user: User, start_date: datetime, end_date: datetime
    ) -> dict:
        """Получает все данные пользователя за период."""
        replies = await self._get_processed_items(
            self._msg_reply_repository.get_replies_by_period_date,
            user.id,
            start_date,
            end_date,
        )

        messages = await self._get_processed_items(
            self._message_repository.get_messages_by_period_date,
            user.id,
            start_date,
            end_date,
        )

        reactions = await self._get_processed_items(
            self._reaction_repository.get_reactions_by_user_and_period,
            user.id,
            start_date,
            end_date,
        )

        logger.info(
            f"Пользователь {user.username}: {len(messages)} сообщений, {len(replies)} ответов, {len(reactions)} реакций"
        )

        return {"replies": replies, "messages": messages, "reactions": reactions}

    def _calculate_user_stats(
        self,
        user: User,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        replies: List[MessageReply],
        start_date: datetime,
        end_date: datetime,
        is_single_day: bool,
    ) -> AllUsersUserStatsResult:
        """Рассчитывает статистику для одного пользователя."""
        if is_single_day:
            day_stats = self._calculate_day_stats(
                messages, reactions, start_date, end_date
            )
            multi_day_stats = None
        else:
            day_stats = None
            multi_day_stats = self._calculate_multi_day_stats(
                messages, reactions, start_date, end_date
            )

        replies_stats = self._calculate_replies_stats(replies)
        breaks = self._calculate_breaks(messages, reactions, is_single_day)

        return AllUsersUserStatsResult(
            user_id=user.id,
            username=user.username,
            day_stats=day_stats,
            multi_day_stats=multi_day_stats,
            replies_stats=replies_stats,
            breaks=breaks,
        )

    def _calculate_day_stats(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[SingleUserDayStats]:
        """Рассчитывает статистику за один день."""
        if not messages and not reactions:
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
        )

    def _calculate_multi_day_stats(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[SingleUserMultiDayStats]:
        """Рассчитывает статистику за несколько дней."""
        if not messages and not reactions:
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
            sorted_messages = sorted(messages, key=lambda m: m.created_at)
            breaks = BreakAnalysisService.calculate_breaks(
                sorted_messages, reactions, is_single_day=True
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
