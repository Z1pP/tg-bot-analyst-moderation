from typing import List, Optional

from constants import MAX_MSG_LENGTH
from dto.report import (
    AllUsersReportResultDTO,
    AllUsersUserStatsResult,
    RepliesStats,
    SingleUserDayStats,
    SingleUserMultiDayStats,
)
from utils.formatter import format_seconds, format_selected_period


class AllUsersReportPresenter:
    """Класс для форматирования данных отчета по всем пользователям в HTML строки"""

    @staticmethod
    def format_report(result: AllUsersReportResultDTO) -> List[str]:
        """
        Форматирует AllUsersReportResultDTO в список HTML строк для отправки.

        Args:
            result: DTO с данными отчета

        Returns:
            Список строк отчета (может быть разбит на части)
        """
        if result.error_message:
            return [result.error_message]

        period_str = format_selected_period(
            start_date=result.start_date, end_date=result.end_date
        )

        if not result.users_stats:
            return ["⚠️ Нет данных за указанный период."]

        user_reports = []
        for user_stats in result.users_stats:
            user_report = AllUsersReportPresenter._format_user_stats(
                user_stats, result.is_single_day, period_str
            )
            user_reports.append(user_report)

        full_report = "\n\n".join(user_reports)

        return AllUsersReportPresenter._split_report(full_report)

    @staticmethod
    def _format_user_stats(
        stats: AllUsersUserStatsResult, is_single_day: bool, period_str: str
    ) -> str:
        """Форматирует статистику одного пользователя."""
        period_prefix = "период " if not is_single_day else ""
        parts = [f"📊 Отчёт: @{stats.username} за {period_prefix}{period_str}"]

        parts.append(
            AllUsersReportPresenter._format_moderation(
                day_stats=stats.day_stats,
                multi_day_stats=stats.multi_day_stats,
                is_single_day=is_single_day,
            )
        )

        parts.append(
            AllUsersReportPresenter._format_messages_and_replies(
                day_stats=stats.day_stats,
                multi_day_stats=stats.multi_day_stats,
                replies_stats=stats.replies_stats,
                is_single_day=is_single_day,
            )
        )

        parts.append(
            AllUsersReportPresenter._format_breaks(stats.breaks, is_single_day)
        )

        if not is_single_day:
            parts.append(
                '❗️Чтобы получить детализацию перерывов по датам, нажмите "Заказ детализации перерывов" под сообщением'
            )

        return "\n\n".join(filter(None, parts))

    @staticmethod
    def _format_moderation(
        day_stats: Optional[SingleUserDayStats],
        multi_day_stats: Optional[SingleUserMultiDayStats],
        is_single_day: bool,
    ) -> str:
        """Форматирует блок модерации."""
        stats = day_stats if is_single_day else multi_day_stats
        warns_count = stats.warns_count if stats else 0
        bans_count = stats.bans_count if stats else 0

        lines = [
            "🚫 Модерация:",
            f"• {warns_count} - выдано предупреждений",
            f"• {bans_count} - выдано банов",
        ]

        return "\n".join(lines)

    @staticmethod
    def _format_messages_and_replies(
        day_stats: Optional[SingleUserDayStats],
        multi_day_stats: Optional[SingleUserMultiDayStats],
        replies_stats: RepliesStats,
        is_single_day: bool,
    ) -> str:
        """Форматирует блок сообщений и ответов."""
        lines = ["💬 Сообщения и ответы:"]

        message_lines = []
        if is_single_day and day_stats:
            if day_stats.first_message_time:
                message_lines.append(
                    f"• {day_stats.first_message_time.strftime('%H:%M')} - 1-е сообщ."
                )
            if day_stats.first_reaction_time:
                message_lines.append(
                    f"• {day_stats.first_reaction_time.strftime('%H:%M')} - 1-я реакция на сообщ."
                )
            if day_stats.last_message_time:
                message_lines.append(
                    f"• {day_stats.last_message_time.strftime('%H:%M')} - последнее сообщ."
                )
            total_messages = day_stats.total_messages
            avg_messages_per_hour = day_stats.avg_messages_per_hour
        elif not is_single_day and multi_day_stats:
            if multi_day_stats.avg_first_message_time:
                message_lines.append(
                    f"• {multi_day_stats.avg_first_message_time} - 1-е сообщ."
                )
            if multi_day_stats.avg_first_reaction_time:
                message_lines.append(
                    f"• {multi_day_stats.avg_first_reaction_time} - 1-я реакция на сообщ."
                )
            if multi_day_stats.avg_last_message_time:
                message_lines.append(
                    f"• {multi_day_stats.avg_last_message_time} - последнее сообщ."
                )
            total_messages = multi_day_stats.total_messages
            avg_messages_per_hour = multi_day_stats.avg_messages_per_hour
        else:
            total_messages = 0
            avg_messages_per_hour = 0

        if message_lines:
            message_lines.append("")

        message_lines.append(f"• {total_messages} - всего сообщ.")
        message_lines.append(f"• {avg_messages_per_hour} - сред. кол-во сообщ./час")

        reply_lines = AllUsersReportPresenter._format_replies_stats(replies_stats)

        lines.extend(message_lines)
        lines.extend(reply_lines)

        return "\n".join(lines)

    @staticmethod
    def _format_replies_stats(stats: RepliesStats) -> List[str]:
        """Форматирует статистику ответов"""
        lines = [f"Из них {stats.total_count} ответов:"]

        if stats.min_time_seconds is not None:
            lines.append(
                f"• {format_seconds(stats.min_time_seconds)} - мин. время отв."
            )
        if stats.max_time_seconds is not None:
            lines.append(
                f"• {format_seconds(stats.max_time_seconds)} - макс. время отв."
            )
        if stats.avg_time_seconds is not None:
            lines.append(
                f"• {format_seconds(stats.avg_time_seconds)} - сред. время отв."
            )
        if stats.median_time_seconds is not None:
            lines.append(
                f"• {format_seconds(stats.median_time_seconds)} - медиан. время отв."
            )

        return lines

    @staticmethod
    def _strip_html_tags(text: str) -> str:
        """Удаляет базовые HTML-теги из строки."""
        return (
            text.replace("<b>", "")
            .replace("</b>", "")
            .replace("<code>", "")
            .replace("</code>", "")
        )

    @staticmethod
    def _format_breaks(breaks: List[str], is_single_day: bool) -> str:
        """Форматирует перерывы"""
        if not breaks:
            return "⏸️ Перерывы: отсутствуют"

        cleaned_breaks = [
            AllUsersReportPresenter._strip_html_tags(line).strip()
            for line in breaks
            if line and line.strip()
        ]

        if not cleaned_breaks:
            return "⏸️ Перерывы: отсутствуют"

        if is_single_day:
            return "⏸️ Перерывы:\n" + "\n".join(cleaned_breaks)

        return "⏸️ Перерывы:\n" + cleaned_breaks[0]

    @staticmethod
    def _split_report(report: str) -> List[str]:
        """
        Разделяет отчет на части по лимиту длины сообщения.

        Args:
            report: Полный текст отчета

        Returns:
            Список частей отчета
        """
        if len(report) <= MAX_MSG_LENGTH:
            return [report]

        parts = report.split("\n\n")
        result = []
        current_part = ""

        for user_report in parts:
            if len(current_part) + len(user_report) + 2 > MAX_MSG_LENGTH:
                if current_part:
                    result.append(current_part)
                current_part = user_report
            else:
                current_part = (
                    f"{current_part}\n\n{user_report}" if current_part else user_report
                )

        if current_part:
            result.append(current_part)

        return result
