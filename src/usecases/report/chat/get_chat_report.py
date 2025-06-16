from datetime import datetime
from statistics import mean, median

from dto.report import ChatReportDTO
from models import ChatMessage, ChatSession, MessageReply
from repositories import ChatRepository, MessageReplyRepository, MessageRepository
from services.break_analysis_service import BreakAnalysisService
from services.work_time_service import WorkTimeService
from utils.formatter import format_seconds, format_selected_period


class GetReportOnSpecificChatUseCase:
    def __init__(
        self,
        msg_reply_repository: MessageReplyRepository,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
    ):
        self._message_repository = message_repository
        self._msg_reply_repository = msg_reply_repository
        self._chat_repostitory = chat_repository

    async def execute(self, dto: ChatReportDTO):
        try:
            chat = await self._chat_repostitory.get_chat_by_title(title=dto.chat_title)

            if not chat:
                raise ValueError("Чат не найден")

            messages = (
                await self._message_repository.get_messages_by_chat_id_and_period(
                    chat_id=chat.id,
                    start_date=dto.start_date,
                    end_date=dto.end_date,
                )
            )

            replies = (
                await self._msg_reply_repository.get_replies_by_chat_id_and_period(
                    chat_id=chat.id,
                    start_date=dto.start_date,
                    end_date=dto.end_date,
                )
            )

            return self._generate_report(
                replies=replies,
                messages=messages,
                chat=chat,
                start_date=dto.start_date,
                end_date=dto.end_date,
                selected_period=dto.selected_period,
            )
        except:
            raise

    def _generate_report(
        self,
        replies: list[MessageReply],
        messages: list[ChatMessage],
        chat: ChatSession,
        start_date: datetime,
        end_date: datetime,
        selected_period: str = None,
    ) -> str:

        if not messages:
            return "\n⚠️ Нет данных за указанный период."

        period = format_selected_period(selected_period)

        total_messages = len(messages)
        messages_per_hour = self._messages_per_hour(len(messages), start_date, end_date)

        total_replies = len(replies)
        response_times = (
            [reply.response_time_seconds for reply in replies] if replies else [0]
        )

        avg_time = mean(response_times)
        median_time = median(response_times)
        min_time = min(response_times)
        max_time = max(response_times)

        working_hours = WorkTimeService.calculate_work_hours(start_date, end_date)

        # Сортируем сообщения по времени
        sorted_messages = sorted(messages, key=lambda r: r.created_at)

        report_lines = []

        # Добавляем информацию о перерывах
        breaks = BreakAnalysisService.calculate_breaks(messages=sorted_messages)

        if breaks:
            report_lines.append("<b>⏸️ Перерывы:</b>")
            for break_info in breaks:
                report_lines.append(f"• {break_info}")
        else:
            report_lines.append("<b>⏸️ Перерывы:</b> отсутствуют")

        breaks = "".join(report_lines)

        # Форматируем отчет
        report = (
            f"<b>📊 Отчёт по: {chat.title} за {period}</b>\n\n"
            f"{self._get_time_first_msg_per_day(messages=messages)}\n"
            f"<b>📈 Статистика по сообщениям:</b>\n"
            f"• {total_messages} - <b>всего сообщений модеров.</b>\n"
            f"• <b>{working_hours}</b> - кол-во рабочих часов\n"
            f"• {messages_per_hour} - сред. кол-во сообщений в час\n\n"
            f"<b>⏱️ Статистика по ответам:</b>\n"
            f"• <b>{total_replies}</b> - всего ответов модеров\n"
            f"• <b>{format_seconds(min_time)}</b> и "
            f"<b>{format_seconds(max_time)}</b> - мин. и макс. время ответов\n"
            f"• <b>{format_seconds(avg_time)}</b> и "
            f"<b>{format_seconds(median_time)}</b> - сред. и медиан. время ответа\n\n"
            "Перерывы:\n"
            f"{breaks}"
        )

        return report

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

    def _get_time_first_msg_per_day(self, messages: list[ChatMessage]) -> str:
        """Возвращает список времени первого сообщения в день."""
        time_first_msg_per_day = []
        times = ""

        for message in messages:
            if message.created_at.date() not in time_first_msg_per_day:
                times += (
                    f"• {message.created_at.strftime('%H:%M')} - первое сообщение "
                    f"{message.created_at.strftime('%d.%m.%Y')}\n"
                )
                time_first_msg_per_day.append(message.created_at.date())

        return times
