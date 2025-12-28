from typing import List

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
        period_prefix = "период " if not result.is_single_day else ""
        report_title = (
            f"<b>📈 Отчет по пользователям за {period_prefix}{period_str}</b>"
        )

        if not result.users_stats:
            return [f"{report_title}\n\n⚠️ Нет данных за указанный период."]

        user_reports = []
        for user_stats in result.users_stats:
            user_report = AllUsersReportPresenter._format_user_stats(
                user_stats, result.is_single_day
            )
            user_reports.append(user_report)

        full_report = "\n\n".join([report_title] + user_reports)

        return AllUsersReportPresenter._split_report(full_report)

    @staticmethod
    def _format_user_stats(stats: AllUsersUserStatsResult, is_single_day: bool) -> str:
        """Форматирует статистику одного пользователя."""
        parts = [f"<b>👤 @{stats.username}</b>"]

        if is_single_day and stats.day_stats:
            parts.append(AllUsersReportPresenter._format_day_stats(stats.day_stats))
        elif not is_single_day and stats.multi_day_stats:
            parts.append(
                AllUsersReportPresenter._format_multi_day_stats(stats.multi_day_stats)
            )

        parts.append(AllUsersReportPresenter._format_replies_stats(stats.replies_stats))

        parts.append(
            AllUsersReportPresenter._format_breaks(stats.breaks, is_single_day)
        )

        return "\n".join(filter(None, parts))

    @staticmethod
    def _format_day_stats(stats: SingleUserDayStats) -> str:
        """Форматирует статистику за один день"""
        lines = []

        if stats.first_message_time:
            lines.append(
                f"• <b>{stats.first_message_time.strftime('%H:%M')}</b> - 1-е сообщение"
            )

        if stats.first_reaction_time:
            lines.append(
                f"• <b>{stats.first_reaction_time.strftime('%H:%M')}</b> - 1-я реакция на сообщение"
            )

        if lines:
            lines.append("")

        lines.extend(
            [
                f"• <b>{stats.avg_messages_per_hour}</b> - сред. кол-во сообщ./час",
                f"• <b>{stats.total_messages}</b> - всего сообщений",
                f"• <b>{stats.warns_count}</b> - выдано варнов",
                f"• <b>{stats.bans_count}</b> - выдано банов",
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def _format_multi_day_stats(stats: SingleUserMultiDayStats) -> str:
        """Форматирует статистику за несколько дней"""
        lines = []

        if stats.avg_first_message_time:
            lines.append(
                f"• <b>{stats.avg_first_message_time}</b> - среднее время отправки 1-х сообщений"
            )

        if stats.avg_first_reaction_time:
            lines.append(
                f"• <b>{stats.avg_first_reaction_time}</b> - среднее время 1-й реакции на сообщение"
            )

        if lines:
            lines.append("")

        lines.extend(
            [
                f"• <b>{stats.avg_messages_per_hour}</b> - сред. кол-во сообщ./час",
                f"• <b>{stats.avg_messages_per_day}</b> - сред. кол-во сообщ./день",
                f"• <b>{stats.total_messages}</b> - всего сообщ. за период",
                f"• <b>{stats.warns_count}</b> - выдано варнов",
                f"• <b>{stats.bans_count}</b> - выдано банов",
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def _format_replies_stats(stats: RepliesStats) -> str:
        """Форматирует статистику ответов"""
        if stats.total_count == 0:
            return "• <b>Нет ответов</b> за указанный период"

        lines = [f"Из них <b>{stats.total_count}</b> ответов:"]

        if stats.min_time_seconds is not None:
            lines.append(
                f"• <b>{format_seconds(stats.min_time_seconds)}</b> - мин. время ответа"
            )
        if stats.max_time_seconds is not None:
            lines.append(
                f"• <b>{format_seconds(stats.max_time_seconds)}</b> - макс. время ответа"
            )
        if stats.avg_time_seconds is not None:
            lines.append(
                f"• <b>{format_seconds(stats.avg_time_seconds)}</b> - сред. время ответа"
            )
        if stats.median_time_seconds is not None:
            lines.append(
                f"• <b>{format_seconds(stats.median_time_seconds)}</b> - медиан. время ответа"
            )

        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _format_breaks(breaks: List[str], is_single_day: bool) -> str:
        """Форматирует перерывы"""
        if is_single_day:
            if not breaks:
                return "<b>⏸️ Перерывы:</b> отсутствуют"
            return "<b>⏸️ Перерывы:</b>\n" + "\n".join(breaks)
        else:
            if not breaks:
                return "<b>⏸️ Перерывы:</b> отсутствуют"
            return "<b>⏸️ Перерывы:</b>\n" + "\n".join(breaks)

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
        title = parts[0]
        user_reports = parts[1:]

        result = [title]
        current_part = ""

        for user_report in user_reports:
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
