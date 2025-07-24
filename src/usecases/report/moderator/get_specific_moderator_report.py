import logging
from datetime import datetime
from statistics import mean, median
from typing import List

from constants import MAX_MSG_LENGTH
from dto.report import ResponseTimeReportDTO
from exceptions.user import UserNotFoundException
from models import ChatMessage, MessageReply, User
from services.break_analysis_service import BreakAnalysisService
from services.work_time_service import WorkTimeService
from utils.formatter import format_seconds, format_selected_period

from .base import BaseReportUseCase

logger = logging.getLogger(__name__)


class GetReportOnSpecificModeratorUseCase(BaseReportUseCase):
    async def execute(self, report_dto: ResponseTimeReportDTO) -> List[str]:
        """
        Генерирует отчет по указанному модератору
        """
        user = await self._user_repository.get_user_by_username(
            username=report_dto.username
        )

        if not user:
            logger.error("Пользователь не найден: %s", report_dto.username)
            raise UserNotFoundException()

        # Получаем сообщения и ответы за указанный период
        replies = await self._get_processed_items(
            repository_method=self._msg_reply_repository.get_replies_by_period_date,
            user_id=user.id,
            start_date=report_dto.start_date,
            end_date=report_dto.end_date,
        )

        logger.info(
            "Получено %d ответов за период %s - %s",
            len(replies),
            report_dto.start_date,
            report_dto.end_date,
        )

        messages = await self._get_processed_items(
            repository_method=self._message_repository.get_messages_by_period_date,
            user_id=user.id,
            start_date=report_dto.start_date,
            end_date=report_dto.end_date,
        )

        logger.info(
            "Получено %d сообщений за период %s - %s",
            len(messages),
            report_dto.start_date,
            report_dto.end_date,
        )

        full_report = self._generate_report(
            replies=replies,
            messages=messages,
            user=user,
            start_date=report_dto.start_date,
            end_date=report_dto.end_date,
            selected_period=report_dto.selected_period,
        )

        return self._split_report(full_report)

    def _generate_report(
        self,
        replies: list[MessageReply],
        messages: list[ChatMessage],
        user: User,
        start_date: datetime,
        end_date: datetime,
        selected_period: str = None,
    ) -> str:
        """Формирует текстовый отчет о времени ответа."""
        period = format_selected_period(selected_period)

        if not messages:
            return "⚠️ Нет данных за указанный период."

        # Сортируем сообщения по времени
        sorted_messages = sorted(messages, key=lambda r: r.created_at)

        # Собираем статистику
        response_times = (
            [reply.response_time_seconds for reply in replies] if replies else [0]
        )
        total_messages = len(messages)
        total_replies = len(replies)

        # Рассчитываем статистику времени ответа
        if response_times:
            avg_time = mean(response_times)
            median_time = median(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
        else:
            avg_time = median_time = min_time = max_time = 0

        # Рассчитываем сообщения в час и время первого сообщения
        messages_per_hour = self._messages_per_hour(
            total_messages, start_date, end_date
        )

        working_hours = WorkTimeService.calculate_work_hours(start_date, end_date)
        # Формируем отчет
        report_lines = [
            f"<b>📈 Отчёт: @{user.username} за {period}</b>\n",
            f"{self.get_time_first_message(messages=messages)}",
            f"• <b>{working_hours}</b> - кол-во рабочих часов\n",
            f"• <b>{total_messages}</b> - всего сообщений",
            f"• <b>{messages_per_hour}</b> - сообщений в час",
            f"• Из них <b>{total_replies}</b> ответ(-ов)",
        ]

        # Добавляем статистику по времени ответа, если есть ответы
        if total_replies > 0:
            report_lines.extend(
                [
                    f"• <b>{format_seconds(min_time)}</b> и "
                    f"<b>{format_seconds(max_time)}</b> - мин. и макс. время ответов",
                    f"• <b>{format_seconds(avg_time)}</b> и "
                    f"<b>{format_seconds(median_time)}</b> - сред. и медиан. время ответа\n",
                ]
            )
        else:
            report_lines.append("• Нет ответов на сообщения\n")

        # Добавляем информацию о перерывах
        breaks = BreakAnalysisService.calculate_breaks(messages=sorted_messages)

        if breaks:
            report_lines.append("<b>⏸️ Перерывы:</b>")
            for break_info in breaks:
                report_lines.append(f"{break_info}")
        else:
            report_lines.append("<b>⏸️ Перерывы:</b> отсутствуют")

        return "\n".join(report_lines)

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

        # Разделяем отчет на заголовок и отчеты по модераторам
        parts = report.split("\n\n")
        title = parts[0]
        moderator_reports = parts[1:] if len(parts) > 1 else []

        result = [title]
        current_part = ""

        # Добавляем отчеты по модераторам
        for mod_report in moderator_reports:
            # Если добавление отчета превысит лимит, создаем новую часть
            if len(current_part) + len(mod_report) + 2 > MAX_MSG_LENGTH:
                if current_part:
                    result.append(current_part)
                current_part = mod_report
            else:
                if current_part:
                    current_part += "\n\n" + mod_report
                else:
                    current_part = mod_report

        # Добавляем последнюю часть
        if current_part:
            result.append(current_part)

        return result
