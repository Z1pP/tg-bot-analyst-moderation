import logging
from datetime import datetime
from typing import Awaitable, Callable, List, TypeVar

from models import ChatMessage, MessageReaction, MessageReply
from repositories import (
    MessageReactionRepository,
    MessageReplyRepository,
    MessageRepository,
    UserRepository,
)
from services.time_service import TimeZoneService
from services.work_time_service import WorkTimeService
from utils.formatter import format_selected_period

T = TypeVar("T", ChatMessage, MessageReply)
logger = logging.getLogger(__name__)


class BaseReportUseCase:
    """Базовый класс для UseCase отчетов"""

    def __init__(
        self,
        msg_reply_repository: MessageReplyRepository,
        message_repository: MessageRepository,
        user_repository: UserRepository,
        reaction_repository: MessageReactionRepository,
    ):
        self._msg_reply_repository = msg_reply_repository
        self._user_repository = user_repository
        self._message_repository = message_repository
        self._reaction_repository = reaction_repository

    async def _get_processed_items(
        self,
        repository_method: Callable[[int, datetime, datetime], Awaitable[List[T]]],
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> List[T]:
        """Получает и обрабатывает элементы из репозитория"""
        items = await repository_method(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        for item in items:
            item.created_at = TimeZoneService.convert_to_local_time(item.created_at)

        return WorkTimeService.filter_by_work_time(items=items)

    def _format_selected_period(self, start_date: datetime, end_date: datetime) -> str:
        """Форматирует выбранный период в читаемый формат"""
        return format_selected_period(start_date, end_date)

    def _messages_per_hour(
        self, messages_count: int, start_date: datetime, end_date: datetime
    ) -> float:
        """Рассчитывает количество сообщений в час рабочего времени."""
        if messages_count < 2:
            return 1

        # Получаем количество рабочих часов между датами
        work_hours = WorkTimeService.calculate_work_hours(start_date, end_date)

        if work_hours <= 0:
            return 1

        return round(messages_count / work_hours, 2)

    def get_time_first_message(self, messages: List[ChatMessage]) -> str:
        """Возвращает время первого сообщения."""
        if not messages:
            return ""

        sorted_messages = sorted(messages, key=lambda m: m.created_at)
        first_message = sorted_messages[0]

        return (
            f"• {first_message.created_at.strftime('%H:%M')} - первое сообщение "
            f"{first_message.created_at.strftime('%d.%m.%Y')}"
        )

    def get_time_first_reaction(self, reactions: List[MessageReaction]) -> str:
        """Возвращает время первой реакции."""
        if not reactions:
            return ""

        sorted_reactions = sorted(reactions, key=lambda r: r.created_at)
        first_reaction = sorted_reactions[0]

        return (
            f"• {first_reaction.created_at.strftime('%H:%M')} - первая реакция "
            f"{first_reaction.created_at.strftime('%d.%m.%Y')}"
        )
