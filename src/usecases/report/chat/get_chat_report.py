from datetime import datetime
from statistics import mean, median
from typing import Awaitable, Callable, List, Optional, TypeVar

from constants import MAX_MSG_LENGTH
from dto.report import ChatReportDTO
from models import ChatMessage, ChatSession, MessageReply
from repositories import ChatRepository, MessageReplyRepository, MessageRepository
from services.break_analysis_service import BreakAnalysisService
from services.time_service import TimeZoneService
from services.work_time_service import WorkTimeService
from utils.formatter import format_seconds, format_selected_period

T = TypeVar("T", ChatMessage, MessageReply)


class GetReportOnSpecificChatUseCase:
    """UseCase для генерации отчета по конкретному чату."""

    def __init__(
        self,
        msg_reply_repository: MessageReplyRepository,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
    ):
        self._message_repository = message_repository
        self._msg_reply_repository = msg_reply_repository
        self._chat_repository = chat_repository

    async def execute(self, dto: ChatReportDTO) -> List[str]:
        """
        Генерирует отчет по конкретному чату за указанный период.

        Args:
            dto: Объект с параметрами для генерации отчета

        Returns:
            Строка с отформатированным отчетом

        Raises:
            ValueError: Если чат не найден
        """
        chat = await self._chat_repository.get_chat_by_title(title=dto.chat_title)
        if not chat:
            raise ValueError("Чат не найден")

        # Получаем сообщения за период
        messages = await self._get_processed_items(
            repository_method=self._message_repository.get_messages_by_chat_id_and_period,
            chat_id=chat.id,
            start_date=dto.start_date,
            end_date=dto.end_date,
        )

        # Получаем ответы за период
        replies = await self._get_processed_items(
            repository_method=self._msg_reply_repository.get_replies_by_chat_id_and_period,
            chat_id=chat.id,
            start_date=dto.start_date,
            end_date=dto.end_date,
        )

        # Генерируем отчет
        report = self._generate_report(
            replies=replies,
            messages=messages,
            chat=chat,
            start_date=dto.start_date,
            end_date=dto.end_date,
            selected_period=dto.selected_period,
        )

        return self._split_report(report=report)

    def _generate_report(
        self,
        replies: List[MessageReply],
        messages: List[ChatMessage],
        chat: ChatSession,
        start_date: datetime,
        end_date: datetime,
        selected_period: Optional[str] = None,
    ) -> str:
        """
        Формирует текстовый отчет на основе полученных данных.
        """
        if not messages:
            return "\n⚠️ Нет данных за указанный период."

        # Основные показатели
        period = format_selected_period(selected_period)
        total_messages = len(messages)
        total_replies = len(replies)
        working_hours = WorkTimeService.calculate_work_hours(start_date, end_date)
        messages_per_hour = self._calculate_messages_per_hour(
            total_messages, working_hours
        )

        # Статистика по времени ответа
        response_stats = self._calculate_response_stats(replies)

        # Информация о первых сообщениях
        first_messages_info = self._get_first_messages_by_day(messages)

        # Информация о перерывах
        breaks_info = self._get_breaks_info(messages)

        # Формируем отчет
        return (
            f"<b>📈 Отчёт по: {chat.title} за {period}</b>\n\n"
            f"{first_messages_info}\n"
            f"• <b>{total_messages}</b> - <b>всего сообщений</b>\n"
            f"• <b>{working_hours}</b> - кол-во рабочих часов\n"
            f"• <b>{messages_per_hour}</b> - сообщений в час\n"
            f"• Из них <b>{total_replies}</b> ответ(-ов)\n"
            f"{response_stats}\n\n"
            f"<code>Подробную информацию о перерывах смотри в отчете модераторов </code>"
            f"<code>за день</code>\n"
            f"{breaks_info}"
        )

    async def _get_processed_items(
        self,
        repository_method: Callable[[int, datetime, datetime], Awaitable[List[T]]],
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> List[T]:
        items = await repository_method(
            chat_id=chat_id,
            start_date=start_date,
            end_date=end_date,
        )

        for item in items:
            item.created_at = TimeZoneService.convert_to_local_time(item.created_at)

        return items

    def _split_report(self, report: str) -> List[str]:
        """
        Разделяет отчет на части, если он превышает максимальную длину.

        Args:
            report: Полный текст отчета

        Returns:
            Список частей отчета
        """
        if len(report) <= MAX_MSG_LENGTH:
            return [report]

        # Разделяем отчет на основную часть и информацию о перерывах

        parts = report.split("Перерывы:\n")
        main_part = parts[0]
        breaks_part = parts[1] if len(parts) > 1 else ""

        result = []

        # Добавляем основную часть
        result.append(main_part + "Перерывы: см. следующее сообщение")

        # Если есть информация о перерывах, разделяем ее на части
        if breaks_part:
            breaks_lines = breaks_part.split("\n")
            current_part = "<b>⏸️ Перерывы:</b>"

            for line in breaks_lines:
                # Если добавление строки превысит лимит, создаем новую часть
                if len(current_part) + len(line) + 1 > MAX_MSG_LENGTH:
                    result.append(current_part)
                    current_part = "<b>⏸️ Перерывы (продолжение):</b>"

                current_part += "\n" + line

            # Добавляем последнюю часть
            if current_part:
                result.append(current_part)

        return result

    def _calculate_messages_per_hour(
        self, messages_count: int, work_hours: float
    ) -> float:
        """Рассчитывает количество сообщений в час рабочего времени."""
        if messages_count < 2 or work_hours <= 0:
            return 1.0
        return round(messages_count / work_hours, 2)

    def _calculate_response_stats(self, replies: List[MessageReply]) -> str:
        """Рассчитывает статистику по времени ответа."""
        if not replies:
            return "• <b>Нет ответов</b> за указанный период"

        response_times = [reply.response_time_seconds for reply in replies]

        avg_time = mean(response_times)
        median_time = median(response_times)
        min_time = min(response_times)
        max_time = max(response_times)

        return (
            f"• <b>{format_seconds(min_time)}</b> и "
            f"<b>{format_seconds(max_time)}</b> - мин. и макс. время ответов\n"
            f"• <b>{format_seconds(avg_time)}</b> и "
            f"<b>{format_seconds(median_time)}</b> - сред. и медиан. время ответа"
        )

    def _get_first_messages_by_day(self, messages: List[ChatMessage]) -> str:
        """Возвращает список времени первого сообщения в день."""
        if not messages:
            return ""

        # Сортируем сообщения по времени
        sorted_messages = sorted(messages, key=lambda m: m.created_at)

        # Группируем по дате
        first_messages_by_day = {}
        for message in sorted_messages:
            date = message.created_at.date()
            if date not in first_messages_by_day:
                first_messages_by_day[date] = message

        # Формируем строки с информацией
        result = []
        for date, message in sorted(first_messages_by_day.items()):
            result.append(
                f"• {message.created_at.strftime('%H:%M')} - первое сообщение "
                f"{message.created_at.strftime('%d.%m.%Y')}"
            )

        return "\n".join(result) + "\n"

    def _get_breaks_info(self, messages: List[ChatMessage]) -> str:
        """Получает информацию о перерывах."""
        if not messages:
            return "<b>⏸️ Перерывы:</b> отсутствуют"

        # Сортируем сообщения по времени
        sorted_messages = sorted(messages, key=lambda m: m.created_at)

        # Получаем перерывы
        breaks = BreakAnalysisService.calculate_breaks(messages=sorted_messages)

        if not breaks:
            return "<b>⏸️ Перерывы:</b> отсутствуют"

        # Формируем строки с информацией
        result = ["<b>⏸️ Перерывы:</b>"]
        for break_info in breaks:
            result.append(f"• {break_info}")

        return "\n".join(result)
