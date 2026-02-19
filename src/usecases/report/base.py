import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import date, datetime, timedelta
from statistics import mean, median
from typing import Any, Awaitable, Callable, List, Optional, Sequence, TypeVar, Union, cast

from pydantic import BaseModel

from constants import MAX_MSG_LENGTH
from constants.period import TimePeriod
from dto.report import RepliesStats, SingleUserDayStats, SingleUserMultiDayStats
from models import ChatMessage, MessageReaction, MessageReply
from repositories import (
    ChatRepository,
    MessageReactionRepository,
    MessageReplyRepository,
    MessageRepository,
    PunishmentRepository,
    UserRepository,
)
from services.break_analysis_service import BreakAnalysisService
from services.time_service import TimeZoneService
from services.work_time_service import WorkTimeService
from utils.formatter import format_selected_period

T = TypeVar("T", ChatMessage, MessageReply, MessageReaction)
logger = logging.getLogger(__name__)


class BaseReportUseCase(ABC):
    """Абстрактный базовый класс для use case отчётов."""

    def __init__(
        self,
        msg_reply_repository: MessageReplyRepository,
        message_repository: MessageRepository,
        user_repository: UserRepository,
        reaction_repository: MessageReactionRepository,
        chat_repository: ChatRepository,
        punishment_repository: PunishmentRepository = None,
    ):
        self._msg_reply_repository = msg_reply_repository
        self._user_repository = user_repository
        self._message_repository = message_repository
        self._reaction_repository = reaction_repository
        self._chat_repository = chat_repository
        self._punishment_repository = punishment_repository

    @abstractmethod
    async def execute(self, dto: BaseModel) -> Any:
        """Абстрактный метод выполнения use case. Принимает DTO из src/dto."""
        ...


    async def _get_processed_items_by_user(
        self,
        repository_method: Callable[[int, datetime, datetime], Awaitable[List[T]]],
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> List[T]:
        """Получает и обрабатывает элементы из репозитория по пользователю."""
        items = await repository_method(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        return self._process_items(items)

    async def _get_processed_items_by_user_in_chats(
        self,
        repository_method,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        chat_ids: List[int],
    ) -> List[T]:
        """Получает и обрабатывает элементы по пользователю в указанных чатах."""
        items = await repository_method(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            chat_ids=chat_ids,
        )
        return self._process_items(items)

    async def _get_processed_items_by_chat_with_users(
        self,
        repository_method,
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
        tracked_user_ids: List[int],
    ) -> List[T]:
        """Получает и обрабатывает элементы по чату с фильтрацией пользователей."""
        items = await repository_method(
            chat_id=chat_id,
            start_date=start_date,
            end_date=end_date,
            tracked_user_ids=tracked_user_ids,
        )
        return self._process_items(items)

    def _process_items(self, items: List[T]) -> List[T]:
        """Обрабатывает элементы: конвертирует время и фильтрует по рабочему времени."""
        for item in items:
            item.created_at = TimeZoneService.convert_to_local_time(item.created_at)
        return cast(
            List[T],
            WorkTimeService.filter_by_work_time(items=items),
        )

    def _format_selected_period(self, start_date: datetime, end_date: datetime) -> str:
        """Форматирует выбранный период в читаемый формат."""
        return format_selected_period(start_date, end_date)

    def _avg_messages_per_hour(
        self,
        messages_count: int,
        start_date: datetime,
        end_date: datetime,
    ) -> float:
        """Рассчитывает среднее количество сообщений в час."""
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
        """Рассчитывает среднее количество сообщений в день."""
        days = max(1, (end_date.date() - start_date.date()).days)
        return round(messages_count / days, 2)

    def get_avg_time_first_messages(self, messages: List[ChatMessage]) -> str:
        """Возвращает среднее время первых сообщений за каждый день."""
        return self._get_avg_time_first_items(items=messages)

    def get_avg_time_first_reaction(self, reactions: List[MessageReaction]) -> str:
        """Возвращает среднее время первых реакций за каждый день."""
        return self._get_avg_time_first_items(items=reactions)

    def _get_avg_time_first_items(
        self,
        items: Sequence[Union[ChatMessage, MessageReaction]],
    ) -> str:
        if not items:
            return ""

        # Находим первые элементы каждого дня
        first_per_day: dict[date, Union[ChatMessage, MessageReaction]] = {}
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

    # --- Общие методы расчёта статистики для отчётов по пользователям ---

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
        last_message_time = None
        if messages:
            first_message = min(messages, key=lambda m: m.created_at)
            first_message_time = first_message.created_at
            last_message = max(messages, key=lambda m: m.created_at)
            last_message_time = last_message.created_at

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
            last_message_time=last_message_time,
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
        avg_last_message_time = self._calculate_avg_daily_end_time(messages)

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
            avg_last_message_time=avg_last_message_time,
            avg_messages_per_hour=avg_messages_per_hour,
            avg_messages_per_day=avg_messages_per_day,
            total_messages=msg_count,
            warns_count=warns_count,
            bans_count=bans_count,
        )

    def _calculate_avg_daily_end_time(
        self, messages: List[ChatMessage]
    ) -> Optional[str]:
        """Возвращает среднее время последнего сообщения за каждый день."""
        if not messages:
            return None

        daily_lasts: dict[date, List[datetime]] = defaultdict(list)
        for message in messages:
            local_time = message.created_at
            daily_lasts[local_time.date()].append(local_time)

        last_times_seconds = []
        for dates_times in daily_lasts.values():
            max_time = max(dates_times).time()
            seconds = max_time.hour * 3600 + max_time.minute * 60 + max_time.second
            last_times_seconds.append(seconds)

        if not last_times_seconds:
            return None

        avg_seconds = int(mean(last_times_seconds))
        hours = avg_seconds // 3600
        minutes = (avg_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"

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
        """Рассчитывает перерывы (однодневный отчёт — детально, многодневный — среднее за день)."""
        if is_single_day:
            sorted_messages = sorted(messages, key=lambda m: m.created_at)
            return BreakAnalysisService.calculate_breaks(
                sorted_messages, reactions, is_single_day=True
            )

        daily_totals = BreakAnalysisService.total_breaks_time_per_day(
            messages, reactions
        )
        if not daily_totals:
            return []

        avg_total = mean(daily_totals)
        formatted_avg = BreakAnalysisService._format_break_time(avg_total)
        return [f"{formatted_avg} - общее время перерыва за день"]

    def _is_single_day_report(
        self,
        selected_period: Optional[str],
        start_date: datetime,
        end_date: datetime,
    ) -> bool:
        """Определяет, является ли отчёт за один день."""
        if selected_period:
            return selected_period in [
                TimePeriod.TODAY.value,
                TimePeriod.YESTERDAY.value,
            ]
        return (end_date.date() - start_date.date()).days <= 1


class UserReportUseCase(BaseReportUseCase):
    """Базовый класс для отчётов по пользователям."""

    async def _get_processed_items(
        self,
        repository_method: Callable[[int, datetime, datetime], Awaitable[List[T]]],
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> List[T]:
        """Обёртка для обратной совместимости: делегирует в _get_processed_items_by_user."""
        return await self._get_processed_items_by_user(
            repository_method, user_id, start_date, end_date
        )


class ChatReportUseCase(BaseReportUseCase):
    """Базовый класс для отчётов по чатам."""

    pass
