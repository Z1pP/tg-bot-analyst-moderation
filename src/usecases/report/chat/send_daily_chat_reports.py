import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from statistics import mean, median
from typing import Any, Awaitable, Callable, Dict, List, Set, TypeVar

from aiogram.exceptions import TelegramAPIError

from constants.dialogs import ReportDialogs
from constants.period import TimePeriod
from exceptions import BotBaseException
from models import ChatMessage, ChatSession, MessageReaction, MessageReply
from models.user import User
from repositories import ChatRepository, MessageRepository, UserRepository
from repositories.message_reply_repository import MessageReplyRepository
from repositories.reaction_repository import MessageReactionRepository
from services import BotMessageService
from services.break_analysis_service import BreakAnalysisService
from services.time_service import TimeZoneService
from services.work_time_service import WorkTimeService
from utils.formatter import format_seconds, format_selected_period

T = TypeVar("T", ChatMessage, MessageReply, MessageReaction)

logger = logging.getLogger(__name__)


class SendDailyChatReportsUseCase:
    """UseCase для автоматической отправки ежедневных отчетов по чатам в архивные чаты."""

    def __init__(
        self,
        chat_repository: ChatRepository,
        user_repository: UserRepository,
        message_repository: MessageRepository,
        msg_reply_repository: MessageReplyRepository,
        reaction_repository: MessageReactionRepository,
        bot_message_service: BotMessageService,
    ):
        self._chat_repository = chat_repository
        self._user_repository = user_repository
        self._message_repository = message_repository
        self._msg_reply_repository = msg_reply_repository
        self._reaction_repository = reaction_repository
        self._bot_message_service = bot_message_service

    async def execute(
        self,
        chat_id: int,
        period: str,
    ) -> None:
        """
        Генерирует и отправляет отчеты по конкретному чату в архивный чат.

        Args:
            chat_id: ID чата, по которому генерируется отчет
            period: Период для отчета (по умолчанию "сегодня")

        """
        logger.info(
            "Начало генерации ежедневного отчета: chat_id=%d, period=%s",
            chat_id,
            period,
        )

        # Получаем чат с архивом
        chat = await self._chat_repository.get_chat_by_id(chat_id=chat_id)
        if not chat:
            logger.warning("Чат не найден: chat_id=%d", chat_id)
            return

        if not chat.archive_chat_id:
            logger.warning("Чат не имеет архива: chat_id=%d", chat_id)
            return

        if not self._has_time_settings(chat=chat):
            await self._notify_admins_missing_settings(chat=chat)
            return

        # Сбор всех отслеживаемых пользователей
        tracked_user_ids = await self._get_all_tracked_user_ids(chat=chat)

        # Определение временного периода
        start_date, end_date = TimePeriod.to_datetime(period)

        adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
            start_date,
            end_date,
            work_start=chat.start_time,
            work_end=chat.end_time,
            tolerance=chat.tolerance,
        )

        # Обработка чата
        try:
            chat_data = await self._fetch_chat_data(
                chat=chat,
                tracked_user_ids=tracked_user_ids,
                start_date=adjusted_start,
                end_date=adjusted_end,
            )
        except BotBaseException as e:
            logger.error(
                "Ошибка при обработке чата %s: %s", chat.title, e, exc_info=True
            )
            return

        report = self._generate_chat_report(
            chat=chat,
            data=chat_data,
            start_date=adjusted_start,
            end_date=adjusted_end,
            tracked_user_ids=tracked_user_ids,
        )

        if report:
            try:
                await self._bot_message_service.send_chat_message(
                    chat_tgid=chat.archive_chat_id,
                    text=report,
                )
            except TelegramAPIError as e:
                logger.error(
                    "Ошибка при отправке отчета в архивный чат %s: %s",
                    chat.title,
                    e,
                    exc_info=True,
                )
            return

    async def _get_all_tracked_user_ids(self, chat: ChatSession) -> List[int]:
        """Собирает ID всех отслеживаемых пользователей для списка чатов."""
        admins_set: Set[User] = set()

        # Получаем админов для чата
        admins = await self._user_repository.get_admins_for_chat(
            chat_tg_id=chat.chat_id
        )
        admins_set.update(admins)

        tracked_users_set: Set[User] = set()
        for admin in admins_set:
            users = await self._user_repository.get_tracked_users_for_admin(
                admin_tg_id=admin.tg_id
            )
            tracked_users_set.update(users)

        return [user.id for user in tracked_users_set]

    async def _fetch_chat_data(
        self,
        chat: ChatSession,
        tracked_user_ids: list[int],
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, List[Any]]:
        """
        Параллельно загружает сообщения, ответы и реакции для конкретного чата.
        """
        # Формируем задачи
        tasks = [
            self._get_processed_items(
                self._message_repository.get_messages_by_chat_id_and_period,
                chat.id,
                start_date,
                end_date,
                tracked_user_ids,
            ),
            self._get_processed_items(
                self._msg_reply_repository.get_replies_by_chat_id_and_period,
                chat.id,
                start_date,
                end_date,
                tracked_user_ids,
            ),
            self._get_processed_items(
                self._reaction_repository.get_reactions_by_chat_and_period,
                chat.id,
                start_date,
                end_date,
                tracked_user_ids,
            ),
        ]

        # Запускаем параллельно
        messages, replies, reactions = await asyncio.gather(*tasks)

        return {
            "messages": messages,
            "replies": replies,
            "reactions": reactions,
        }

    async def _get_processed_items(
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
            item.created_at = TimeZoneService.convert_to_local_time(dt=item.created_at)
        return items

    def _generate_chat_report(
        self,
        chat: ChatSession,
        data: Dict[str, List[Any]],
        start_date: datetime,
        end_date: datetime,
        tracked_user_ids: list[int],
    ) -> str:
        messages = data["messages"]
        replies = data["replies"]
        reactions = data["reactions"]

        period_text = format_selected_period(start_date=start_date, end_date=end_date)
        report_parts = [f"<b>📈 Отчёт: «{chat.title}» за {period_text}</b>\n"]

        if not tracked_user_ids:
            report_parts.append("⚠️ Нет пользователей в отслеживании.")
        elif not messages and not reactions:
            report_parts.append("⚠️ Нет данных за указанный период.")
        else:
            stats = self._generate_users_stats_by_chat(
                messages=messages,
                replies=replies,
                reactions=reactions,
                start_date=start_date,
                end_date=end_date,
                chat=chat,
            )
            report_parts.append(stats)

        return "\n".join(filter(None, report_parts))

    def _generate_users_stats_by_chat(
        self,
        messages: List[ChatMessage],
        replies: List[MessageReply],
        reactions: List[MessageReaction],
        start_date: datetime,
        end_date: datetime,
        chat: ChatSession,
    ) -> str:
        # Группировка данных по пользователям
        users_data = defaultdict(
            lambda: {"messages": [], "replies": [], "reactions": []}
        )
        user_names: Dict[int, str] = {}

        # Функция для извлечения имени пользователя
        def get_username(user_obj, user_id):
            if user_id in user_names:
                return user_names[user_id]
            name = (
                user_obj.username
                if user_obj and hasattr(user_obj, "username") and user_obj.username
                else f"user_{user_id}"
            )
            user_names[user_id] = name
            return name

        # Группировка сообщений
        for msg in messages:
            uid = msg.user_id
            users_data[uid]["messages"].append(msg)
            get_username(msg.user, uid)

        # Группировка ответов
        for reply in replies:
            uid = reply.reply_user_id
            users_data[uid]["replies"].append(reply)
            # В реплаях может не быть объекта user, если он не загружен,
            # поэтому имя берем, только если юзер уже встречался, или пробуем извлечь
            if uid not in user_names and hasattr(reply, "user"):
                get_username(reply.user, uid)

        # Группировка реакций
        for reaction in reactions:
            uid = reaction.user_id
            users_data[uid]["reactions"].append(reaction)
            get_username(reaction.user, uid)

        # Генерация отчетов
        user_reports = []
        for user_id, stats in users_data.items():
            if not stats["messages"] and not stats["reactions"]:
                continue

            # Добавление имени пользователя в статистику для генератора
            stats["username"] = user_names.get(user_id, f"user_{user_id}")

            user_report = self._generate_user_report(
                data=stats,
                start_date=start_date,
                end_date=end_date,
                chat=chat,
            )
            user_reports.append(user_report)

        if not user_reports:
            return "⚠️ Нет активности за указанный период"

        return "\n\n".join(user_reports)

    def _generate_user_report(
        self, data: dict, start_date: datetime, end_date: datetime, chat: ChatSession
    ) -> str:
        username = data.get("username")
        messages = data.get("messages")
        replies = data.get("replies")
        reactions = data.get("reactions")

        parts = [f"@{username}:"]

        # Основная статистика
        parts.append(
            self._generate_single_day_stats(
                messages, reactions, start_date, end_date, chat
            )
        )

        # Статистика ответов
        parts.append(self._generate_replies_stats(replies))

        # Перерывы
        parts.append(
            self._generate_breaks_section(messages, reactions, chat.breaks_time)
        )

        return "\n".join(filter(None, parts))

    def _generate_single_day_stats(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        start_date: datetime,
        end_date: datetime,
        chat: ChatSession,
    ) -> str:
        stats = []

        if messages:
            first_msg_time = min(m.created_at for m in messages)
            stats.append(f"• <b>{first_msg_time.strftime('%H:%M')}</b> — 1-е сообщение")

        if reactions:
            first_reaction_time = min(r.created_at for r in reactions)
            stats.append(
                f"• <b>{first_reaction_time.strftime('%H:%M')}</b> — 1-я реакция на сообщение"
            )

        if stats:
            stats.append("")

        msg_count = len(messages)
        # Вычисляем рабочие часы один раз
        working_hours = WorkTimeService.calculate_work_hours(
            start_date=start_date,
            end_date=end_date,
            work_start=chat.start_time,
            work_end=chat.end_time,
        )
        avg_per_hour = round(msg_count / working_hours, 2) if working_hours > 0 else 0

        stats.extend(
            [
                f"• <b>{avg_per_hour}</b> — сред. кол-во сообщ./час",
                f"• <b>{msg_count}</b> — всего сообщений",
            ]
        )

        return "\n".join(stats)

    def _generate_replies_stats(self, replies: List[MessageReply]) -> str:
        if not replies:
            return "Из них всего <b>0</b> ответов"

        times = [r.response_time_seconds for r in replies]
        # Предварительные расчеты, чтобы не считать дважды в f-строке
        min_t, max_t = min(times), max(times)
        avg_t, med_t = int(mean(times)), int(median(times))

        return "\n".join(
            [
                f"Из них всего <b>{len(replies)}</b> ответов:",
                f"• <b>{format_seconds(min_t)}</b> — мин. время ответа",
                f"• <b>{format_seconds(max_t)}</b> — макс. время ответа",
                f"• <b>{format_seconds(avg_t)}</b> — сред. время ответа",
                f"• <b>{format_seconds(med_t)}</b> — медиан. время ответа",
            ]
        )

    def _generate_breaks_section(
        self,
        messages: List[ChatMessage],
        reactions: List[MessageReaction],
        breaks_time: int,
    ) -> str:
        if not messages and not reactions:
            return "<b>⏸️ Перерывы:</b> отсутствуют"

        # Сортировка здесь важна для алгоритма анализа перерывов
        sorted_messages = sorted(messages, key=lambda m: m.created_at)

        breaks = BreakAnalysisService.calculate_breaks(
            messages=sorted_messages,
            reactions=reactions,
            is_single_day=True,
            min_break_minutes=breaks_time,
        )

        if breaks:
            return "<b>⏸️ Перерывы:</b>\n" + "\n".join(breaks)
        return "<b>⏸️ Перерывы:</b> отсутствуют"

    async def _notify_admins_missing_settings(self, chat: ChatSession) -> None:
        admins = await self._user_repository.get_admins_for_chat(
            chat_tg_id=chat.chat_id
        )
        if not admins:
            logger.warning(
                "Не найдены админы для уведомления о настройках: chat_id=%d",
                chat.id,
            )
            return

        text = ReportDialogs.CHAT_REPORT_SETTINGS_REQUIRED_ADMIN.format(
            chat_title=chat.title or "Без названия"
        )
        for admin in admins:
            await self._bot_message_service.send_private_message(
                user_tgid=admin.tg_id,
                text=text,
            )

    @staticmethod
    def _has_time_settings(chat: ChatSession) -> bool:
        return (
            chat.start_time is not None
            and chat.end_time is not None
            and chat.tolerance is not None
            and chat.breaks_time is not None
        )
