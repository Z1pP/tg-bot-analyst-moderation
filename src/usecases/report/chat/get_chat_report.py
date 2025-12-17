import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from statistics import mean, median
from typing import Any, Awaitable, Callable, List, Optional, TypeVar

from constants.dialogs import ReportDialogs
from constants.enums import AdminActionType
from constants.period import TimePeriod
from dto.report import (
    ChatReportDTO,
    RepliesStats,
    ReportResultDTO,
    UserDayStats,
    UserMultiDayStats,
    UserStatsDTO,
)
from models import ChatMessage, ChatSession, MessageReaction, MessageReply
from repositories import (
    ChatRepository,
    MessageReactionRepository,
    MessageReplyRepository,
    MessageRepository,
    UserRepository,
)
from services import AdminActionLogService
from services.break_analysis_service import BreakAnalysisService
from services.time_service import TimeZoneService
from services.work_time_service import WorkTimeService
from utils.formatter import format_selected_period

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class ChatData:
    messages: List[ChatMessage]
    reactions: List[MessageReaction]
    replies: List[MessageReply]


class GetChatReportUseCase:
    """Usecase for generation chat report"""

    """
    1. Получаем чат
    2. Получаем отслеживаемых пользователей для админа
    3. Получаем данные о сообщениях, реакциях и ответах за период для отслеживаемых пользователей
    4. Трансформируем период в даты
    5. К датам добавляем время из чата

    """

    def __init__(
        self,
        chat_repository: ChatRepository,
        user_repository: UserRepository,
        message_repository: MessageRepository,
        reaction_repository: MessageReactionRepository,
        msg_reply_repository: MessageReplyRepository,
        admin_action_log_service: AdminActionLogService = None,
    ) -> None:
        self._chat_repository = chat_repository
        self._user_repository = user_repository
        self._message_repository = message_repository
        self._reaction_repository = reaction_repository
        self._msg_reply_repository = msg_reply_repository
        self._admin_action_log_service = admin_action_log_service

    async def execute(self, dto: ChatReportDTO) -> ReportResultDTO:
        chat = await self._chat_repository.get_chat_by_id(chat_id=dto.chat_id)

        if not chat:
            # Для ошибки вычисляем даты из периода для корректного DTO
            start_date, end_date = TimePeriod.to_datetime(period=dto.selected_period)
            return ReportResultDTO(
                users_stats=[],
                chat_title="",
                start_date=start_date,
                end_date=end_date,
                is_single_day=False,
                working_hours=0.0,
                error_message=ReportDialogs.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
            )

        tracked_users_ids = await self._get_tracked_users_ids(
            admin_tg_id=dto.admin_tg_id
        )

        # Вычисляем даты до проверки tracked_users для корректного DTO
        # Если даты уже заданы (из календаря), используем их, иначе вычисляем из периода
        if dto.start_date and dto.end_date:
            # Даты из календаря - корректируем по рабочим часам
            dto.start_date, dto.end_date = WorkTimeService.adjust_dates_to_work_hours(
                start_date=dto.start_date,
                end_date=dto.end_date,
                work_start=chat.start_time,
                work_end=chat.end_time,
                tolerance=chat.tolerance,
            )
        else:
            # Вычисляем из периода
            dto.start_date, dto.end_date = await self._get_currect_dates(
                period=dto.selected_period,
                chat=chat,
            )

        if not tracked_users_ids:
            return ReportResultDTO(
                users_stats=[],
                chat_title=chat.title or "",
                start_date=dto.start_date,
                end_date=dto.end_date,
                is_single_day=False,
                working_hours=0.0,
                error_message=ReportDialogs.NO_TRACKED_USERS,
            )

        chat_data = await self._get_chat_data(
            chat_id=chat.id,
            dto=dto,
            tracked_user_ids=tracked_users_ids,
        )

        if not chat_data.messages and not chat_data.reactions:
            return ReportResultDTO(
                users_stats=[],
                chat_title=chat.title or "",
                start_date=dto.start_date,
                end_date=dto.end_date,
                is_single_day=False,
                working_hours=0.0,
                error_message=ReportDialogs.NO_DATA_FOR_REPORT,
            )

        is_single_day = self._is_single_day_report(
            selected_period=dto.selected_period,
            start_date=dto.start_date,
            end_date=dto.end_date,
        )

        working_hours = WorkTimeService.calculate_work_hours(
            start_date=dto.start_date,
            end_date=dto.end_date,
            work_start=chat.start_time,
            work_end=chat.end_time,
        )

        users_stats = await self._calculate_users_stats(
            data=chat_data,
            start_date=dto.start_date,
            end_date=dto.end_date,
            is_single_day=is_single_day,
            working_hours=working_hours,
        )

        # Логирование действия администратора
        await self._log_admin_action(dto, chat)

        return ReportResultDTO(
            users_stats=users_stats,
            chat_title=chat.title or "",
            start_date=dto.start_date,
            end_date=dto.end_date,
            is_single_day=is_single_day,
            working_hours=working_hours,
        )

    async def _get_tracked_users_ids(self, admin_tg_id: str) -> list[int]:
        tracked_users = await self._user_repository.get_tracked_users_for_admin(
            admin_tg_id=admin_tg_id
        )
        return [user.id for user in tracked_users]

    async def _get_chat_data(
        self,
        chat_id: int,
        dto: ChatReportDTO,
        tracked_user_ids: list[int],
    ) -> ChatData:
        """
        Получает все данные чата параллельно.
        """
        # Формируем список задач
        tasks = [
            self._get_processed_items_with_users(
                self._message_repository.get_messages_by_chat_id_and_period,
                chat_id,
                dto.start_date,
                dto.end_date,
                tracked_user_ids,
            ),
            self._get_processed_items_with_users(
                self._reaction_repository.get_reactions_by_chat_and_period,
                chat_id,
                dto.start_date,
                dto.end_date,
                tracked_user_ids,
            ),
            self._get_processed_items_with_users(
                self._msg_reply_repository.get_replies_by_chat_id_and_period,
                chat_id,
                dto.start_date,
                dto.end_date,
                tracked_user_ids,
            ),
        ]

        messages, reactions, replies = await asyncio.gather(*tasks)

        data = ChatData(messages=messages, reactions=reactions, replies=replies)

        logger.info(
            "Чат %d: %d сообщений, %d ответов, %d реакций",
            chat_id,
            len(messages),
            len(replies),
            len(reactions),
        )

        return data

    async def _get_processed_items_with_users(
        self,
        repository_method: Callable[..., Awaitable[List[T]]],
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
        tracked_user_ids: list[int],
    ) -> List[T]:
        """
        Получает элементы из репозитория без мутации исходных объектов.
        Время конвертируется "на лету" при расчетах через _get_local_time.
        """
        items = await repository_method(
            chat_id=chat_id,
            start_date=start_date,
            end_date=end_date,
            tracked_user_ids=tracked_user_ids,
        )
        # Не мутируем исходные объекты - конвертация времени будет происходить "на лету"
        return items

    @staticmethod
    def _get_local_time(item: Any) -> datetime:
        """
        Возвращает локальное время для элемента без мутации исходного объекта.

        Args:
            item: Элемент с полем created_at

        Returns:
            Конвертированное локальное время
        """
        if hasattr(item, "created_at"):
            return TimeZoneService.convert_to_local_time(dt=item.created_at)
        return item.created_at if hasattr(item, "created_at") else datetime.now()

    async def _transform_period_to_dates(
        self, period: str
    ) -> tuple[datetime, datetime]:
        return TimePeriod.to_datetime(period=period)

    async def _get_currect_dates(
        self, period: str, chat: ChatSession
    ) -> tuple[datetime, datetime]:
        start_date, end_date = TimePeriod.to_datetime(period=period)

        return WorkTimeService.adjust_dates_to_work_hours(
            start_date=start_date,
            end_date=end_date,
            work_start=chat.start_time,
            work_end=chat.end_time,
            tolerance=chat.tolerance,
        )

    async def _calculate_users_stats(
        self,
        data: ChatData,
        start_date: datetime,
        end_date: datetime,
        is_single_day: bool,
        working_hours: float,
    ) -> List[UserStatsDTO]:
        """
        Оптимизированный расчет статистики по пользователям за один проход.
        Группирует данные по user_id и создает UserStatsDTO.
        """
        # Используем defaultdict для группировки за один проход
        users_data: dict[int, dict[str, list]] = defaultdict(
            lambda: {"messages": [], "replies": [], "reactions": []}
        )
        user_names: dict[int, str] = {}

        # Функция-хелпер для получения имени
        def resolve_username(user_obj, uid):
            if uid not in user_names:
                user_names[uid] = (
                    user_obj.username
                    if user_obj and hasattr(user_obj, "username") and user_obj.username
                    else f"user_{uid}"
                )

        # Один проход по всем данным для группировки
        for msg in data.messages:
            uid = msg.user_id
            users_data[uid]["messages"].append(msg)
            resolve_username(msg.user, uid)

        for reply in data.replies:
            uid = reply.reply_user_id
            users_data[uid]["replies"].append(reply)
            if uid not in user_names and hasattr(reply, "user"):
                resolve_username(reply.user, uid)

        for reaction in data.reactions:
            uid = reaction.user_id
            users_data[uid]["reactions"].append(reaction)
            resolve_username(reaction.user, uid)

        # Создаем UserStatsDTO для каждого пользователя
        users_stats = []
        for user_id, stats in users_data.items():
            if not stats["messages"] and not stats["reactions"]:
                continue

            username = user_names.get(user_id, f"user_{user_id}")

            # Рассчитываем статистику
            if is_single_day:
                day_stats = self._calculate_single_day_stats(
                    stats["messages"], stats["reactions"], working_hours
                )
                multi_day_stats = None
            else:
                day_stats = None
                multi_day_stats = self._calculate_multi_day_stats(
                    stats["messages"],
                    stats["reactions"],
                    start_date,
                    end_date,
                    working_hours,
                )

            replies_stats = self._calculate_replies_stats(stats["replies"])

            # Рассчитываем перерывы
            breaks = self._calculate_breaks(
                stats["messages"], stats["reactions"], is_single_day
            )

            users_stats.append(
                UserStatsDTO(
                    user_id=user_id,
                    username=username,
                    day_stats=day_stats,
                    multi_day_stats=multi_day_stats,
                    replies_stats=replies_stats,
                    breaks=breaks,
                )
            )

        return users_stats

    def _calculate_single_day_stats(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        working_hours: float,
    ) -> UserDayStats:
        """Рассчитывает статистику за один день"""
        first_message_time = None
        first_reaction_time = None

        if messages:
            # Используем _get_local_time для конвертации без мутации
            first_msg = min(messages, key=lambda m: self._get_local_time(m))
            first_message_time = self._get_local_time(first_msg)

        if reactions:
            first_reaction = min(reactions, key=lambda r: self._get_local_time(r))
            first_reaction_time = self._get_local_time(first_reaction)

        msg_count = len(messages)
        avg_per_hour = round(msg_count / working_hours, 2) if working_hours > 0 else 0

        return UserDayStats(
            first_message_time=first_message_time,
            first_reaction_time=first_reaction_time,
            avg_messages_per_hour=avg_per_hour,
            total_messages=msg_count,
        )

    def _calculate_multi_day_stats(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        start_date: datetime,
        end_date: datetime,
        working_hours: float,
    ) -> UserMultiDayStats:
        """Рассчитывает статистику за несколько дней"""
        avg_first_message_time = None
        avg_first_reaction_time = None

        if messages:
            avg_first_message_time = self._calculate_avg_daily_start_time(messages)

        if reactions:
            avg_first_reaction_time = self._calculate_avg_daily_start_time(reactions)

        msg_count = len(messages)
        days = (end_date.date() - start_date.date()).days + 1

        avg_per_hour = round(msg_count / working_hours, 2) if working_hours > 0 else 0
        avg_per_day = round(msg_count / days, 2) if days > 0 else 0

        return UserMultiDayStats(
            avg_first_message_time=avg_first_message_time,
            avg_first_reaction_time=avg_first_reaction_time,
            avg_messages_per_hour=avg_per_hour,
            avg_messages_per_day=avg_per_day,
            total_messages=msg_count,
        )

    def _calculate_avg_daily_start_time(self, items: List[Any]) -> Optional[str]:
        """
        Универсальный метод для расчета среднего времени первого действия за день.
        Использует _get_local_time для конвертации без мутации.
        """
        if not items:
            return None

        daily_firsts = defaultdict(list)
        for item in items:
            local_time = self._get_local_time(item)
            daily_firsts[local_time.date()].append(local_time)

        first_times_seconds = []
        for dates_times in daily_firsts.values():
            min_time = min(dates_times).time()
            seconds = min_time.hour * 3600 + min_time.minute * 60 + min_time.second
            first_times_seconds.append(seconds)

        if not first_times_seconds:
            return None

        avg_seconds = int(mean(first_times_seconds))
        hours = avg_seconds // 3600
        minutes = (avg_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"

    def _calculate_replies_stats(self, replies: List[MessageReply]) -> RepliesStats:
        """Рассчитывает статистику ответов"""
        if not replies:
            return RepliesStats(
                total_count=0,
                min_time_seconds=None,
                max_time_seconds=None,
                avg_time_seconds=None,
                median_time_seconds=None,
            )

        times = [r.response_time_seconds for r in replies]
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
        """
        Рассчитывает перерывы. Возвращает список строк, уже отформатированных
        BreakAnalysisService.
        BreakAnalysisService конвертирует время внутри, поэтому передаем оригинальные объекты.
        """
        if not messages and not reactions:
            return []

        # BreakAnalysisService конвертирует время внутри, но требует отсортированные сообщения
        # Сортируем по оригинальному created_at (BreakAnalysisService конвертирует внутри)
        sorted_messages = sorted(messages, key=lambda m: m.created_at)

        if is_single_day:
            # Для однодневного отчета возвращаем список строк перерывов
            breaks = BreakAnalysisService.calculate_breaks(
                messages=sorted_messages,
                reactions=reactions,
                is_single_day=is_single_day,
            )
            return breaks
        else:
            # Для многодневного отчета возвращаем одну строку со средним временем
            avg_time = BreakAnalysisService.avg_breaks_time(messages, reactions)
            if avg_time:
                return [
                    f"Перерывы:\n• <b>{avg_time}</b> — средн.время перерыва между сообщ. и реакциями"
                ]
            return []

    def _is_single_day_report(
        self,
        selected_period: Optional[str],
        start_date: datetime,
        end_date: datetime,
    ) -> bool:
        from constants.period import TimePeriod

        if selected_period in [TimePeriod.TODAY.value, TimePeriod.YESTERDAY.value]:
            return True
        return (end_date.date() - start_date.date()).days < 1

    def is_single_day_report(self, report_dto: ChatReportDTO) -> bool:
        # Публичный метод-обертка для использования извне, если нужно
        return self._is_single_day_report(
            report_dto.selected_period, report_dto.start_date, report_dto.end_date
        )

    async def _log_admin_action(self, dto: ChatReportDTO, chat: ChatSession):
        period = format_selected_period(
            start_date=dto.start_date, end_date=dto.end_date
        )
        details = f"Чат: {chat.title}, Период: {period}"
        await self._admin_action_log_service.log_action(
            admin_tg_id=dto.admin_tg_id,
            action_type=AdminActionType.REPORT_CHAT,
            details=details,
        )
