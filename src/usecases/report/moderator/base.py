import logging
from datetime import datetime
from typing import Awaitable, Callable, List, TypeVar

from models import ChatMessage, MessageReply
from repositories import (
    MessageReplyRepository,
    MessageRepository,
    UserRepository,
)
from services.time_service import TimeZoneService
from services.work_time_service import WorkTimeService

T = TypeVar("T", ChatMessage, MessageReply)
logger = logging.getLogger(__name__)


class BaseReportUseCase:
    """Базовый класс для UseCase отчетов"""

    def __init__(
        self,
        msg_reply_repository: MessageReplyRepository,
        message_repository: MessageRepository,
        user_repository: UserRepository,
    ):
        self._msg_reply_repository = msg_reply_repository
        self._user_repository = user_repository
        self._message_repository = message_repository

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

    def _format_selected_period(self, selected_period: str) -> str:
        """Форматирует выбранный период в читаемый формат"""
        if not selected_period:
            return "<b>указанный период</b>"
        return selected_period.split("За")[-1].strip()

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
