import logging
from datetime import datetime
from statistics import mean, median
from typing import List

from dto.report import AllModeratorReportDTO
from models import ChatMessage, MessageReply, User
from services.break_analysis_service import BreakAnalysisService
from services.time_service import TimeZoneService

from .base import BaseReportUseCase

logger = logging.getLogger(__name__)


class GetAllModeratorsReportUseCase(BaseReportUseCase):
    async def execute(self, dto: AllModeratorReportDTO) -> str:
        users = await self._user_repository.get_all_users()

        if not users:
            logger.error("Количество найденных модераторов = %s", len(users))
            return "⚠️ Не выбран не один модератор!"

        selected_period = self._format_selected_period(dto.selected_period)
        report_title = f"<b>📈 Отчет по модераторам за {selected_period}</b>"

        reports = []
        for user in users:
            # Получаем и обрабатываем данные для отчета
            replies = await self._get_processed_items(
                repository_method=self._msg_reply_repository.get_replies_by_period_date,
                user_id=user.id,
                start_date=dto.start_date,
                end_date=dto.end_date,
            )

            logger.info(
                "Получено %d ответов за период %s - %s",
                len(replies),
                dto.start_date,
                dto.end_date,
            )

            messages = await self._get_processed_items(
                repository_method=self._message_repository.get_messages_by_period_date,
                user_id=user.id,
                start_date=dto.start_date,
                end_date=dto.end_date,
            )

            logger.info(
                "Получено %d сообщений за период %s - %s",
                len(messages),
                dto.start_date,
                dto.end_date,
            )

            if not messages:
                continue

            report = self._generate_report(
                replies=replies,
                messages=messages,
                user=user,
                start_date=dto.start_date,
                end_date=dto.end_date,
            )

            reports.append(report)

        return "\n\n".join([report_title] + reports)

    def _generate_report(
        self,
        replies: List[MessageReply],
        messages: List[ChatMessage],
        user: User,
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Создает отчет для одного модератора"""
        if not messages:
            return f"<b>👤 @{user.username}</b>\n" "Нет сообщений за указанный период"

        sorted_messages = sorted(messages, key=lambda r: r.created_at)

        # Базовая статистика
        total_message = len(messages)
        total_replies = len(replies)
        time_first_message = TimeZoneService.format_time(sorted_messages[0].created_at)

        # Сообщений в час
        avg_message_per_hour = self._messages_per_hour(
            total_message, start_date, end_date
        )

        # Статистика времени ответа
        response_times = (
            [reply.response_time_seconds for reply in replies] if replies else [0]
        )
        if response_times and response_times != [0]:
            avg_time = round(mean(response_times), 2)
            median_time = round(median(response_times), 2)
            min_time = round(min(response_times), 2)
            max_time = round(max(response_times), 2)
            response_stats = [
                f"• <b>{min_time} сек.</b> и <b>{max_time / 60:.2f} мин.</b> - мин. и макс. время ответа",
                f"• <b>{avg_time} сек.</b> и <b>{median_time} сек.</b> - сред. и медиан. время ответа",
            ]
        else:
            response_stats = []

        # Формируем отчет
        report = [
            f"<b>👤 @{user.username}</b>\n",
            f"Первое сообщение {time_first_message}\n",
            f"• <b>{total_message}</b> - всего сообщений",
            f"• <b>{avg_message_per_hour:.2f}</b> - сред. кол-во сообщ. в час",
        ]

        if total_replies > 0:
            report.append(f"• Из них <b>{total_replies}</b> ответов")
            report.extend(response_stats)
        else:
            report.append("• <b>Нет ответов</b> за указанный период")

        report.append("")

        # Добавляем перерывы
        breaks = BreakAnalysisService.calculate_breaks(messages=sorted_messages)

        if breaks:
            report.append("<b>⏸️ Перерывы:</b>")
            for break_info in breaks:
                report.append(f"• {break_info}")
        else:
            report.append("<b>⏸️ Перерывы:</b> отсутствуют")

        return "\n".join(report)
