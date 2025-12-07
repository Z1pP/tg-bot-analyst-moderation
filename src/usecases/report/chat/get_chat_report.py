import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from statistics import mean, median
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar

from constants import MAX_MSG_LENGTH
from constants.enums import AdminActionType
from dto.report import ChatReportDTO
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
from utils.formatter import format_seconds, format_selected_period

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class ChatData:
    messages: List[ChatMessage]
    reactions: List[MessageReaction]
    replies: List[MessageReply]


class GetReportOnSpecificChatUseCase:
    """UseCase для генерации отчета по конкретному чату."""

    def __init__(
        self,
        msg_reply_repository: MessageReplyRepository,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
        reaction_repository: MessageReactionRepository,
        user_repository: UserRepository,
        admin_action_log_service: AdminActionLogService = None,
    ):
        self._message_repository = message_repository
        self._msg_reply_repository = msg_reply_repository
        self._chat_repository = chat_repository
        self._reaction_repository = reaction_repository
        self._user_repository = user_repository
        self._admin_action_log_service = admin_action_log_service

    async def execute(self, dto: ChatReportDTO) -> List[str]:
        """Генерирует отчет по конкретному чату за указанный период."""
        chat = await self._get_chat(chat_id=dto.chat_id)

        tracked_users = await self._user_repository.get_tracked_users_for_admin(
            admin_tg_id=dto.admin_tg_id,
        )
        tracked_user_ids = [user.id for user in tracked_users]

        # Параллельная загрузка данных
        chat_data = await self._get_chat_data(
            chat=chat,
            dto=dto,
            tracked_user_ids=tracked_user_ids,
        )

        report = self._generate_report(
            data=chat_data,
            chat=chat,
            start_date=dto.start_date,
            end_date=dto.end_date,
            selected_period=dto.selected_period,
            tracked_user_ids=tracked_user_ids,
        )

        report_parts = self._split_report(report=report)

        # Логирование действия
        if self._admin_action_log_service:
            await self._log_admin_action(dto, chat)

        return report_parts

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

    async def _get_chat(self, chat_id: int) -> ChatSession:
        chat = await self._chat_repository.get_chat_by_id(chat_id=chat_id)
        if not chat:
            raise ValueError("Чат не найден")
        return chat

    async def _get_chat_data(
        self,
        chat: ChatSession,
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
                chat.id,
                dto.start_date,
                dto.end_date,
                tracked_user_ids,
            ),
            self._get_processed_items_with_users(
                self._reaction_repository.get_reactions_by_chat_and_period,
                chat.id,
                dto.start_date,
                dto.end_date,
                tracked_user_ids,
            ),
            self._get_processed_items_with_users(
                self._msg_reply_repository.get_replies_by_chat_id_and_period,
                chat.id,
                dto.start_date,
                dto.end_date,
                tracked_user_ids,
            ),
        ]

        # Выполняем запросы параллельно
        messages, reactions, replies = await asyncio.gather(*tasks)

        data = ChatData(messages=messages, reactions=reactions, replies=replies)

        logger.info(
            "Чат %s: %d сообщений, %d ответов, %d реакций",
            chat.title,
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
        items = await repository_method(
            chat_id=chat_id,
            start_date=start_date,
            end_date=end_date,
            tracked_user_ids=tracked_user_ids,
        )
        # Конвертация времени
        for item in items:
            if hasattr(item, "created_at"):
                item.created_at = TimeZoneService.convert_to_local_time(
                    dt=item.created_at
                )
        return items

    def _generate_report(
        self,
        data: ChatData,
        chat: ChatSession,
        start_date: datetime,
        end_date: datetime,
        selected_period: Optional[str] = None,
        tracked_user_ids: list[int] = None,
    ) -> str:
        if not tracked_user_ids:
            return "⚠️ Нет пользователей в отслеживании."

        if not data.messages and not data.reactions:
            return "⚠️ Нет данных за указанный период."

        is_single_day = self._is_single_day_report(
            selected_period=selected_period,
            start_date=start_date,
            end_date=end_date,
        )

        period_str = format_selected_period(start_date=start_date, end_date=end_date)
        period_prefix = "период " if not is_single_day else ""

        # Вычисляем рабочие часы один раз для всех пользователей
        working_hours = WorkTimeService.calculate_work_hours(
            start_date=start_date, end_date=end_date
        )

        report_parts = [
            f"<b>📈 Отчёт: «{chat.title}» за {period_prefix}{period_str}</b>\n",
            self._generate_users_stats_by_chat(
                data=data,
                start_date=start_date,
                end_date=end_date,
                is_single_day=is_single_day,
                working_hours=working_hours,
            ),
        ]

        return "\n".join(filter(None, report_parts))

    def _generate_users_stats_by_chat(
        self,
        data: ChatData,
        start_date: datetime,
        end_date: datetime,
        is_single_day: bool,
        working_hours: float,
    ) -> str:
        """Генерирует статистику по пользователям в чате"""
        users_data = defaultdict(
            lambda: {"messages": [], "replies": [], "reactions": []}
        )
        user_names: Dict[int, str] = {}

        # Функция-хелпер для получения имени
        def resolve_username(user_obj, uid):
            if uid in user_names:
                return
            user_names[uid] = (
                user_obj.username
                if user_obj and hasattr(user_obj, "username") and user_obj.username
                else f"user_{uid}"
            )

        # 1. Сообщения
        for msg in data.messages:
            uid = msg.user_id
            users_data[uid]["messages"].append(msg)
            resolve_username(msg.user, uid)

        # 2. Ответы
        for reply in data.replies:
            uid = reply.reply_user_id
            users_data[uid]["replies"].append(reply)
            # В reply может не быть подгружен user, проверяем
            if uid not in user_names and hasattr(reply, "user"):
                resolve_username(reply.user, uid)

        # 3. Реакции
        for reaction in data.reactions:
            uid = reaction.user_id
            users_data[uid]["reactions"].append(reaction)
            resolve_username(reaction.user, uid)

        # Генерация отчета
        user_reports = []
        for user_id, stats in users_data.items():
            if not stats["messages"] and not stats["reactions"]:
                continue

            stats["username"] = user_names.get(user_id, f"user_{user_id}")

            user_report = self._generate_single_user_report(
                stats=stats,
                start_date=start_date,
                end_date=end_date,
                is_single_day=is_single_day,
                working_hours=working_hours,
            )
            user_reports.append(user_report)

        if not user_reports:
            return "⚠️ Нет активности за указанный период"

        result = "\n\n".join(user_reports)

        if not is_single_day:
            result += "\n\n❗Чтобы получить детализацию перерывов по датам, нажмите соответствующую кнопку"

        return result

    def _generate_single_user_report(
        self,
        stats: dict,
        start_date: datetime,
        end_date: datetime,
        is_single_day: bool,
        working_hours: float,
    ) -> str:
        username = stats.get("username")
        messages = stats.get("messages")
        replies = stats.get("replies")
        reactions = stats.get("reactions")

        report_parts = [f"@{username}:"]

        if is_single_day:
            report_parts.append(
                self._generate_single_day_stats(messages, reactions, working_hours)
            )
        else:
            report_parts.append(
                self._generate_multi_day_stats(
                    messages, reactions, start_date, end_date, working_hours
                )
            )

        report_parts.append(self._generate_replies_stats(replies))

        if is_single_day:
            report_parts.append(
                self._generate_breaks_section(messages, reactions, is_single_day=True)
            )
        else:
            report_parts.append(
                self._generate_breaks_multiday_section(messages, reactions)
            )

        return "\n".join(filter(None, report_parts))

    def _generate_single_day_stats(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        working_hours: float,
    ) -> str:
        stats = []
        if messages:
            first_msg = min(messages, key=lambda m: m.created_at)
            stats.append(
                f"• <b>{first_msg.created_at.strftime('%H:%M')}</b> — 1-е сообщение"
            )

        if reactions:
            first_reaction = min(reactions, key=lambda r: r.created_at)
            stats.append(
                f"• <b>{first_reaction.created_at.strftime('%H:%M')}</b> — 1-я реакция на сообщение"
            )

        stats.append("")

        msg_count = len(messages)
        avg_per_hour = round(msg_count / working_hours, 2) if working_hours > 0 else 0

        stats.extend(
            [
                f"• <b>{avg_per_hour}</b> — сред. кол-во сообщ./час",
                f"• <b>{msg_count}</b> — всего сообщений",
            ]
        )
        return "\n".join(stats)

    def _generate_multi_day_stats(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        start_date: datetime,
        end_date: datetime,
        working_hours: float,
    ) -> str:
        stats = []

        if messages:
            avg_time = self._calculate_avg_daily_start_time(messages)
            stats.append(f"• <b>{avg_time}</b> — среднее время отправки 1-х сообщений")

        if reactions:
            avg_time = self._calculate_avg_daily_start_time(reactions)
            stats.append(
                f"• <b>{avg_time}</b> — среднее время 1-й реакции на сообщение"
            )

        stats.append("")

        msg_count = len(messages)
        days = (end_date.date() - start_date.date()).days + 1

        avg_per_hour = round(msg_count / working_hours, 2) if working_hours > 0 else 0
        avg_per_day = round(msg_count / days, 2) if days > 0 else 0

        stats.extend(
            [
                f"• <b>{avg_per_hour}</b> — сред. кол-во сообщ./час",
                f"• <b>{avg_per_day}</b> — сред. кол-во сообщ./день",
                f"• <b>{msg_count}</b> — всего сообщ. за период",
            ]
        )
        return "\n".join(stats)

    def _calculate_avg_daily_start_time(self, items: List[Any]) -> str:
        """Универсальный метод для расчета среднего времени первого действия за день."""
        if not items:
            return "н/д"

        daily_firsts = defaultdict(list)
        for item in items:
            daily_firsts[item.created_at.date()].append(item.created_at)

        first_times_seconds = []
        for dates_times in daily_firsts.values():
            min_time = min(dates_times).time()
            seconds = min_time.hour * 3600 + min_time.minute * 60 + min_time.second
            first_times_seconds.append(seconds)

        if not first_times_seconds:
            return "н/д"

        avg_seconds = int(mean(first_times_seconds))
        hours = avg_seconds // 3600
        minutes = (avg_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"

    def _generate_replies_stats(self, replies: List[MessageReply]) -> str:
        if not replies:
            return "Из них всего <b>0</b> ответов"

        times = [r.response_time_seconds for r in replies]
        return "\n".join(
            [
                f"Из них всего <b>{len(replies)}</b> ответов:",
                f"• <b>{format_seconds(min(times))}</b> — мин. время ответа",
                f"• <b>{format_seconds(max(times))}</b> — макс. время ответа",
                f"• <b>{format_seconds(int(mean(times)))}</b> — сред. время ответа",
                f"• <b>{format_seconds(int(median(times)))}</b> — медиан. время ответа",
            ]
        )

    def _generate_breaks_section(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        is_single_day: bool = False,
    ) -> str:
        if not messages and not reactions:
            return "<b>⏸️ Перерывы:</b> отсутствуют"

        sorted_messages = sorted(messages, key=lambda m: m.created_at)
        breaks = BreakAnalysisService.calculate_breaks(
            messages=sorted_messages,
            reactions=reactions,
            is_single_day=is_single_day,
        )

        if breaks:
            return "<b>⏸️ Перерывы:</b>\n" + "\n".join(breaks)
        return "<b>⏸️ Перерывы:</b> отсутствуют"

    def _generate_breaks_multiday_section(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
    ) -> str:
        avg_time = BreakAnalysisService.avg_breaks_time(messages, reactions)
        if avg_time:
            return f"Перерывы:\n• <b>{avg_time}</b> — средн.время перерыва между сообщ. и реакциями"
        return "Перерывы: отсутствуют"

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

    def _split_report(self, report: str) -> List[str]:
        if len(report) <= MAX_MSG_LENGTH:
            return [report]

        parts = report.split("<b>⏸️ Перерывы:</b>")
        main_part = parts[0]
        breaks_part = parts[1] if len(parts) > 1 else ""

        result = [main_part + "Перерывы: см. следующее сообщение"]

        if breaks_part:
            # Разбиваем перерывы построчно
            current_part = "<b>⏸️ Перерывы:</b>"
            for line in breaks_part.split("\n"):
                if not line:
                    continue
                # +1 для учета переноса строки
                if len(current_part) + len(line) + 1 > MAX_MSG_LENGTH:
                    result.append(current_part)
                    current_part = "<b>⏸️ Перерывы (продолжение):</b>"
                current_part += "\n" + line

            result.append(current_part)

        return result
