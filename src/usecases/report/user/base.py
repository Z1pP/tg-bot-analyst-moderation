import logging
from datetime import datetime, timedelta
from statistics import mean
from typing import Awaitable, Callable, List, TypeVar, Union

from constants import MAX_MSG_LENGTH
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

T = TypeVar("T", ChatMessage, MessageReply, MessageReaction)
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

    def _avg_messages_per_hour(
        self,
        messages_count: int,
        start_date: datetime,
        end_date: datetime,
    ) -> float:
        """Рассчитывает среднее количество сообщений в час"""
        # Получаем количество рабочих часов между датами
        work_hours = WorkTimeService.calculate_work_hours(start_date, end_date)

        if work_hours <= 0:
            return 1

        return round(messages_count / work_hours, 2)

    def _avg_message_per_day(
        self,
        messages_count: int,
        start_date: datetime,
        end_date: datetime,
    ) -> float:
        """Расчитывет среднее количество сообщений в день"""
        days = max(1, (end_date.date() - start_date.date()).days)
        return round(messages_count / days, 2)

    def get_time_first_message(self, messages: List[ChatMessage]) -> str:
        """Возвращает время первого сообщения."""
        return self._get_time_first_item(messages)

    def get_time_first_reaction(self, reactions: List[MessageReaction]) -> str:
        """Возвращает время первой реакции."""
        return self._get_time_first_item(reactions)

    def _get_time_first_item(
        self, items: List[Union[ChatMessage, MessageReaction]]
    ) -> str:
        """Возвращает время первого элемента."""
        return (
            min(items, key=lambda x: x.created_at).created_at.strftime("%H:%M")
            if items
            else ""
        )

    def get_avg_time_first_messages(self, messages: List[ChatMessage]) -> str:
        """Возвращает среднее время первых сообщений на каждый день"""
        return self._get_avg_time_first_items(items=messages)

    def get_avg_time_first_reaction(self, reactions: List[MessageReaction]) -> str:
        """Возвращает среднее время первых реакций на каждый день"""
        return self._get_avg_time_first_items(items=reactions)

    def _get_avg_time_first_items(
        self,
        items: List[Union[ChatMessage, MessageReaction]],
    ) -> str:
        if not items:
            return ""

        # Находим первые элементы каждого дня
        first_per_day = {}
        for item in items:
            day = item.created_at.date()
            if (
                day not in first_per_day
                or item.created_at < first_per_day[day].created_at
            ):
                first_per_day[day] = item

        if not first_per_day:
            return ""

        # Преобразуем время в секунды с начала дня
        seconds_list = [
            item.created_at.time().hour * 3600
            + item.created_at.time().minute * 60
            + item.created_at.time().second
            for item in first_per_day.values()
        ]

        avg_seconds = int(mean(seconds_list))
        return (datetime.min + timedelta(seconds=avg_seconds)).strftime("%H:%M")

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
