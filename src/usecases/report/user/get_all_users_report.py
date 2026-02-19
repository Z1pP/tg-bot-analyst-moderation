import logging
from datetime import datetime
from typing import List, Optional

from constants.enums import AdminActionType
from constants.work_time import END_TIME, START_TIME, TOLERANCE
from dto.report import (
    AllUsersReportDTO,
    AllUsersReportResultDTO,
    AllUsersUserStatsResult,
)
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
from services.work_time_service import WorkTimeService
from utils.collection_utils import group_by

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
        punishment_repository: PunishmentRepository,
        admin_action_log_service: Optional[AdminActionLogService] = None,
    ) -> None:
        super().__init__(
            msg_reply_repository,
            message_repository,
            user_repository,
            reaction_repository,
            chat_repository,
            punishment_repository,
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

        users_stats = []

        # Получаем статистику наказаний для всех пользователей за период
        user_ids = [user.id for user in users]
        all_punishment_stats = (
            await self._punishment_repository.get_punishment_counts_by_moderators(
                moderator_ids=user_ids,
                start_date=adjusted_start,
                end_date=adjusted_end,
            )
        )

        users_data = await self._get_all_users_data(
            user_ids=user_ids,
            start_date=adjusted_start,
            end_date=adjusted_end,
        )

        for user in users:
            user_data = users_data.get(
                user.id, {"messages": [], "reactions": [], "replies": []}
            )
            punishment_stats = all_punishment_stats.get(
                user.id, {"warns": 0, "bans": 0}
            )

            if (
                not user_data["messages"]
                and not user_data["reactions"]
                and punishment_stats["warns"] == 0
                and punishment_stats["bans"] == 0
            ):
                continue

            user_stats = self._calculate_user_stats(
                user=user,
                messages=user_data["messages"],
                reactions=user_data["reactions"],
                replies=user_data["replies"],
                start_date=adjusted_start,
                end_date=adjusted_end,
                is_single_day=is_single_day,
                warns_count=punishment_stats["warns"],
                bans_count=punishment_stats["bans"],
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

    async def _get_all_users_data(
        self,
        user_ids: List[int],
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """Получает все данные пользователей за период одной выборкой."""
        replies = await self._msg_reply_repository.get_replies_by_period_date_for_users(
            user_ids=user_ids,
            start_date=start_date,
            end_date=end_date,
        )
        messages = await self._message_repository.get_messages_by_period_date_for_users(
            user_ids=user_ids,
            start_date=start_date,
            end_date=end_date,
        )
        reactions = (
            await self._reaction_repository.get_reactions_by_user_and_period_for_users(
                user_ids=user_ids,
                start_date=start_date,
                end_date=end_date,
            )
        )

        replies = self._process_items(replies)
        messages = self._process_items(messages)
        reactions = self._process_items(reactions)

        replies_by_user = group_by(replies, lambda r: r.reply_user_id)
        messages_by_user = group_by(messages, lambda m: m.user_id)
        reactions_by_user = group_by(reactions, lambda r: r.user_id)

        return {
            user_id: {
                "replies": replies_by_user.get(user_id, []),
                "messages": messages_by_user.get(user_id, []),
                "reactions": reactions_by_user.get(user_id, []),
            }
            for user_id in user_ids
        }

    def _calculate_user_stats(
        self,
        user: User,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        replies: List[MessageReply],
        start_date: datetime,
        end_date: datetime,
        is_single_day: bool,
        warns_count: int = 0,
        bans_count: int = 0,
    ) -> AllUsersUserStatsResult:
        """Рассчитывает статистику для одного пользователя."""
        if is_single_day:
            day_stats = self._calculate_day_stats(
                messages,
                reactions,
                start_date,
                end_date,
                warns_count=warns_count,
                bans_count=bans_count,
            )
            multi_day_stats = None
        else:
            day_stats = None
            multi_day_stats = self._calculate_multi_day_stats(
                messages,
                reactions,
                start_date,
                end_date,
                warns_count=warns_count,
                bans_count=bans_count,
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
