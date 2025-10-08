import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from statistics import mean, median
from typing import Awaitable, Callable, List, Optional, TypeVar

from constants import MAX_MSG_LENGTH
from dto.report import ChatReportDTO
from models import ChatMessage, ChatSession, MessageReaction, MessageReply
from repositories import (
    ChatRepository,
    MessageReactionRepository,
    MessageReplyRepository,
    MessageRepository,
    UserRepository,
)
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
    ):
        self._message_repository = message_repository
        self._msg_reply_repository = msg_reply_repository
        self._chat_repository = chat_repository
        self._reaction_repository = reaction_repository
        self._user_repository = user_repository

    async def execute(self, dto: ChatReportDTO) -> List[str]:
        """Генерирует отчет по конкретному чату за указанный период."""
        chat = await self._get_chat(chat_id=dto.chat_id)
        tracked_users = await self._user_repository.get_tracked_users_for_admin(
            admin_tg_id=dto.admin_tg_id,
        )
        tracked_user_ids = [user.id for user in tracked_users]
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

        return self._split_report(report=report)

    async def _get_chat(self, chat_id: int) -> ChatSession:
        """Получает чат по названию."""
        chat = await self._chat_repository.get_chat(chat_id=chat_id)
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
        Получает все данные чата (сообщения. ответы, реакции) за период для
        отслеживаемых пользователей.
        """

        methods = {
            "messages": self._message_repository.get_messages_by_chat_id_and_period,
            "replies": self._msg_reply_repository.get_replies_by_chat_id_and_period,
            "reactions": self._reaction_repository.get_reactions_by_chat_and_period,
        }

        results = {}
        for key, method in methods.items():
            results[key] = await self._get_processed_items_with_users(
                repository_method=method,
                chat_id=chat.id,
                start_date=dto.start_date,
                end_date=dto.end_date,
                tracked_user_ids=tracked_user_ids,
            )

        data = ChatData(**results)

        logger.info(
            "Чат %s: %d сообщений, %d ответов, %d реакций",
            chat.title,
            len(data.messages),
            len(data.replies),
            len(data.reactions),
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
        """Получает и обрабатывает элементы из репозитория с фильтрацией по пользователям."""
        items = await repository_method(
            chat_id=chat_id,
            start_date=start_date,
            end_date=end_date,
            tracked_user_ids=tracked_user_ids,
        )

        for item in items:
            item.created_at = TimeZoneService.convert_to_local_time(dt=item.created_at)

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
        """Формирует текстовый отчет."""
        messages, replies, reactions = (
            data.messages,
            data.replies,
            data.reactions,
        )

        # Проверяем наличие отслеживаемых пользователей
        if not tracked_user_ids:
            return "⚠️ Нет пользователей в отслеживании."

        if not messages and not reactions:
            return "⚠️ Нет данных за указанный период."

        # Определяем тип отчета
        is_single_day = self._is_single_day_report(
            selected_period=selected_period,
            start_date=start_date,
            end_date=end_date,
        )

        period = format_selected_period(start_date=start_date, end_date=end_date)
        period_text = "период " if not is_single_day else ""

        report_parts = [
            f"<b>📈 Отчёт: «{chat.title}» за {period_text}{period}</b>\n",
            self._generate_users_stats_by_chat(
                messages=messages,
                replies=replies,
                reactions=reactions,
                start_date=start_date,
                end_date=end_date,
                is_single_day=is_single_day,
            ),
        ]

        return "\n".join(filter(None, report_parts))

    def _generate_basic_stats(
        self,
        messages: List[ChatMessage],
        replies: List[MessageReply],
        reactions: List[MessageReaction],
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Генерирует базовую статистику."""
        stats_parts = []

        # Первые сообщения по дням
        if messages:
            first_messages_info = self._get_first_messages_by_day(messages=messages)
            stats_parts.append(first_messages_info)

        # Статистика активности
        working_hours = WorkTimeService.calculate_work_hours(
            start_date=start_date, end_date=end_date
        )
        total_activity = len(messages) + len(reactions)
        activity_per_hour = self._calculate_activity_per_hour(
            activity_count=total_activity, work_hours=working_hours
        )

        stats_parts.extend(
            [
                f"• <b>{len(messages)}</b> - всего сообщений",
                f"• <b>{len(reactions)}</b> - всего реакций",
                f"• <b>{working_hours}</b> - кол-во рабочих часов",
                f"• <b>{activity_per_hour}</b> - активности в час",
                f"• Из них <b>{len(replies)}</b> ответ(-ов)\n",
            ]
        )

        return "\n".join(stats_parts)

    def _generate_breaks_section(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        is_single_day: bool = False,
    ) -> str:
        """Генерирует секцию с перерывами."""
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

    def _get_first_messages_by_day(self, messages: List[ChatMessage]) -> str:
        """Возвращает список времени первого сообщения в день."""
        if not messages:
            return ""

        sorted_messages = sorted(messages, key=lambda m: m.created_at)
        first_messages_by_day = {}

        for message in sorted_messages:
            date = message.created_at.date()
            if date not in first_messages_by_day:
                first_messages_by_day[date] = message

        result = []
        for date, message in sorted(first_messages_by_day.items()):
            result.append(
                f"• {message.created_at.strftime('%H:%M')} - первое сообщение "
                f"{message.created_at.strftime('%d.%m.%Y')}"
            )

        return "\n".join(result) + "\n"

    def _generate_users_stats_by_chat(
        self,
        messages: List[ChatMessage],
        replies: List[MessageReply],
        reactions: List[MessageReaction],
        start_date: datetime,
        end_date: datetime,
        is_single_day: bool,
    ) -> str:
        """Генерирует статистику по пользователям в чате"""
        # Группируем данные по пользователям
        users_data = {}

        # Группируем сообщения по пользователям
        for message in messages:
            user_id = message.user_id
            if user_id not in users_data:
                # Извлекаем username сразу, пока сессия активна
                username = (
                    message.user.username
                    if (
                        message.user
                        and hasattr(message.user, "username")
                        and message.user.username
                    )
                    else f"user_{user_id}"
                )
                users_data[user_id] = {
                    "username": username,
                    "messages": [],
                    "replies": [],
                    "reactions": [],
                }
            users_data[user_id]["messages"].append(message)

        # Группируем ответы
        for reply in replies:
            user_id = reply.reply_user_id
            if user_id in users_data:
                users_data[user_id]["replies"].append(reply)

        # Группируем реакции
        for reaction in reactions:
            user_id = reaction.user_id
            if user_id not in users_data:
                # Извлекаем username сразу, пока сессия активна
                username = (
                    reaction.user.username
                    if (
                        reaction.user
                        and hasattr(reaction.user, "username")
                        and reaction.user.username
                    )
                    else f"user_{user_id}"
                )
                users_data[user_id] = {
                    "username": username,
                    "messages": [],
                    "replies": [],
                    "reactions": [],
                }
            users_data[user_id]["reactions"].append(reaction)

        # Генерируем отчет по каждому пользователю
        user_reports = []
        for user_id, data in users_data.items():
            if not data["messages"] and not data["reactions"]:
                continue

            user_report = self._generate_single_user_report(
                data=data,
                start_date=start_date,
                end_date=end_date,
                is_single_day=is_single_day,
            )
            user_reports.append(user_report)

        if not user_reports:
            return "⚠️ Нет активности за указанный период"

        result = "\n\n".join(user_reports)

        # Добавляем призыв к детализации для многодневных отчетов
        if not is_single_day:
            result += "\n\n❗Чтобы получить детализацию перерывов по датам, нажмите соответствующую кнопку"

        return result

    def _generate_single_user_report(
        self,
        data: dict,
        start_date: datetime,
        end_date: datetime,
        is_single_day: bool,
    ) -> str:
        username = data.get("username")
        messages = data.get("messages")
        replies = data.get("replies")
        reactions = data.get("reactions")

        report_parts = [f"@{username}:"]

        # Статистика сообщений и реакций
        if is_single_day:
            stats = self._generate_single_day_stats(
                messages=messages,
                reactions=reactions,
                start_date=start_date,
                end_date=end_date,
            )
        else:
            stats = self._generate_multi_day_stats(
                messages=messages,
                reactions=reactions,
                start_date=start_date,
                end_date=end_date,
            )

        report_parts.append(stats)

        # Статистика ответов
        replies_stats = self._generate_replies_stats(replies=replies)
        report_parts.append(replies_stats)

        # Перерывы
        if is_single_day:
            breaks_stats = self._generate_breaks_section(
                messages=messages,
                reactions=reactions,
                is_single_day=is_single_day,
            )
        else:
            breaks_stats = self._generate_breaks_multiday_section(
                messages=messages,
                reactions=reactions,
            )

        report_parts.append(breaks_stats)

        return "\n".join(filter(None, report_parts))

    def _generate_single_day_stats(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        start_date: datetime,
        end_date: datetime,
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
        working_hours = WorkTimeService.calculate_work_hours(
            start_date=start_date, end_date=end_date
        )
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
    ) -> str:
        stats = []

        # Среднее время первых сообщений
        if messages:
            avg_first_msg_time = self._get_avg_first_message_time(messages=messages)
            stats.append(
                f"• <b>{avg_first_msg_time}</b> — среднее время отправки 1-х сообщений"
            )

        if reactions:
            avg_first_reaction_time = self._get_avg_first_reaction_time(
                reactions=reactions
            )
            stats.append(
                f"• <b>{avg_first_reaction_time}</b> — среднее время 1-й реакции на сообщение"
            )

        stats.append("")

        msg_count = len(messages)
        working_hours = WorkTimeService.calculate_work_hours(
            start_date=start_date, end_date=end_date
        )
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

    def _generate_replies_stats(
        self,
        replies: List[MessageReply],
    ) -> str:
        if not replies:
            return "Из них всего <b>0</b> ответов"

        times = [reply.response_time_seconds for reply in replies]
        return "\n".join(
            [
                f"Из них всего <b>{len(replies)}</b> ответов:",
                f"• <b>{format_seconds(seconds=min(times))}</b> — мин. время ответа",
                f"• <b>{format_seconds(seconds=max(times))}</b> — макс. время ответа",
                f"• <b>{format_seconds(seconds=int(mean(times)))}</b> — сред. время ответа",
                f"• <b>{format_seconds(seconds=int(median(times)))}</b> — медиан. время ответа",
            ]
        )

    def _generate_breaks_multiday_section(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
    ) -> str:
        avg_breaks_time = BreakAnalysisService.avg_breaks_time(
            messages=messages, reactions=reactions
        )
        if avg_breaks_time:
            return (
                f"Перерывы:\n• <b>{avg_breaks_time}</b> — средн."
                "время перерыва между сообщ. и реакциями"
            )
        return "Перерывы: отсутствуют"

    def _get_avg_first_message_time(
        self,
        messages: List[ChatMessage],
    ) -> str:
        from collections import defaultdict

        daily_first_messages = defaultdict(list)
        for message in messages:
            date = message.created_at.date()
            daily_first_messages[date].append(message)

        first_times = []
        for date, msgs in daily_first_messages.items():
            first_msg = min(msgs, key=lambda m: m.created_at)
            first_times.append(first_msg.created_at.time())

        if not first_times:
            return "н/д"

        # Вычисляем среднее время
        total_seconds = sum(
            t.hour * 3600 + t.minute * 60 + t.second for t in first_times
        )
        avg_seconds = total_seconds // len(first_times)

        hours = avg_seconds // 3600
        minutes = (avg_seconds % 3600) // 60

        return f"{hours:02d}:{minutes:02d}"

    def _get_avg_first_reaction_time(
        self,
        reactions: List[MessageReaction],
    ) -> str:

        daily_first_reactions = defaultdict(list)
        for reaction in reactions:
            date = reaction.created_at.date()
            daily_first_reactions[date].append(reaction)

        first_times = []
        for date, reacts in daily_first_reactions.items():
            first_react = min(reacts, key=lambda r: r.created_at)
            first_times.append(first_react.created_at.time())

        if not first_times:
            return "н/д"

        # Вычисляем среднее время
        total_seconds = sum(
            t.hour * 3600 + t.minute * 60 + t.second for t in first_times
        )
        avg_seconds = total_seconds // len(first_times)

        hours = avg_seconds // 3600
        minutes = (avg_seconds % 3600) // 60

        return f"{hours:02d}:{minutes:02d}"

    def _is_single_day_report(
        self,
        selected_period: str,
        start_date: datetime,
        end_date: datetime,
    ) -> bool:
        from constants.period import TimePeriod

        if selected_period:
            return selected_period in [
                TimePeriod.TODAY.value,
                TimePeriod.YESTERDAY.value,
            ]

        return (end_date.date() - start_date.date()).days <= 1

    def is_single_day_report(
        self,
        report_dto: ChatReportDTO,
    ) -> bool:
        return self._is_single_day_report(
            selected_period=report_dto.selected_period,
            start_date=report_dto.start_date,
            end_date=report_dto.end_date,
        )

    def _calculate_activity_per_hour(
        self,
        activity_count: int,
        work_hours: float,
    ) -> float:
        """Рассчитывает количество активности в час рабочего времени."""
        if activity_count < 1 or work_hours <= 0:
            return 0.0
        return round(activity_count / work_hours, 2)

    def _split_report(self, report: str) -> List[str]:
        """Разделяет отчет на части по лимиту длины."""
        if len(report) <= MAX_MSG_LENGTH:
            return [report]

        parts = report.split("<b>⏸️ Перерывы:</b>")
        main_part = parts[0]
        breaks_part = parts[1] if len(parts) > 1 else ""

        result = [main_part + "Перерывы: см. следующее сообщение"]

        if breaks_part:
            breaks_lines = breaks_part.split("\n")
            current_part = "<b>⏸️ Перерывы:</b>"

            for line in breaks_lines:
                if len(current_part) + len(line) + 1 > MAX_MSG_LENGTH:
                    result.append(current_part)
                    current_part = "<b>⏸️ Перерывы (продолжение):</b>"
                current_part += "\n" + line

            if current_part:
                result.append(current_part)

        return result
