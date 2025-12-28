from typing import List

from constants import MAX_MSG_LENGTH
from dto.report import (
    RepliesStats,
    ReportResultDTO,
    UserDayStats,
    UserMultiDayStats,
    UserStatsDTO,
)
from utils.formatter import format_seconds, format_selected_period


class ReportPresenter:
    """Класс для форматирования данных отчета в HTML строки"""

    @staticmethod
    def format_report(result: ReportResultDTO) -> List[str]:
        """
        Форматирует ReportResultDTO в список HTML строк для отправки.

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

        header = (
            f"<b>📈 Отчёт: «{result.chat_title}» за {period_prefix}{period_str}</b>\n\n"
        )

        if (
            result.active_users
            and result.active_users[0] > 0
            and result.active_users[1] > 0
        ):
            header += f"Активных пользователей {result.active_users[0]} из {result.active_users[1]}\n\n"

        if not result.users_stats:
            return [f"{header}⚠️ Нет активности за указанный период"]

        user_reports = []
        for user_stats in result.users_stats:
            user_report = ReportPresenter.format_user_stats(
                user_stats, result.is_single_day
            )
            user_reports.append(user_report)

        report_body = "\n\n".join(user_reports)

        if not result.is_single_day:
            report_body += "\n\n❗Чтобы получить детализацию перерывов по датам, нажмите соответствующую кнопку"

        full_report = f"{header}{report_body}"

        return ReportPresenter._split_report(full_report)

    @staticmethod
    def format_user_stats(stats: UserStatsDTO, is_single_day: bool) -> str:
        """
        Форматирует статистику одного пользователя в HTML строку.

        Args:
            stats: Статистика пользователя
            is_single_day: Флаг однодневного отчета

        Returns:
            Отформатированная строка со статистикой пользователя
        """
        parts = [f"@{stats.username}:"]

        if is_single_day and stats.day_stats:
            parts.append(ReportPresenter._format_day_stats(stats.day_stats))
        elif not is_single_day and stats.multi_day_stats:
            parts.append(ReportPresenter._format_multi_day_stats(stats.multi_day_stats))

        parts.append(ReportPresenter._format_replies_stats(stats.replies_stats))

        if stats.breaks:
            if is_single_day:
                parts.append(ReportPresenter._format_breaks_single_day(stats.breaks))
            else:
                parts.append(ReportPresenter._format_breaks_multiday(stats.breaks))
        else:
            if is_single_day:
                parts.append("<b>⏸️ Перерывы:</b> отсутствуют")
            else:
                parts.append("Перерывы: отсутствуют")

        return "\n".join(filter(None, parts))

    @staticmethod
    def _format_day_stats(stats: UserDayStats) -> str:
        """Форматирует статистику за один день"""
        lines = []

        if stats.first_message_time:
            lines.append(
                f"• <b>{stats.first_message_time.strftime('%H:%M')}</b> — 1-е сообщение"
            )

        if stats.first_reaction_time:
            lines.append(
                f"• <b>{stats.first_reaction_time.strftime('%H:%M')}</b> — 1-я реакция на сообщение"
            )

        if lines:
            lines.append("")

        lines.extend(
            [
                f"• <b>{stats.avg_messages_per_hour}</b> — сред. кол-во сообщ./час",
                f"• <b>{stats.total_messages}</b> — всего сообщений",
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def _format_multi_day_stats(stats: UserMultiDayStats) -> str:
        """Форматирует статистику за несколько дней"""
        lines = []

        if stats.avg_first_message_time:
            lines.append(
                f"• <b>{stats.avg_first_message_time}</b> — среднее время отправки 1-х сообщений"
            )

        if stats.avg_first_reaction_time:
            lines.append(
                f"• <b>{stats.avg_first_reaction_time}</b> — среднее время 1-й реакции на сообщение"
            )

        if lines:
            lines.append("")

        lines.extend(
            [
                f"• <b>{stats.avg_messages_per_hour}</b> — сред. кол-во сообщ./час",
                f"• <b>{stats.avg_messages_per_day}</b> — сред. кол-во сообщ./день",
                f"• <b>{stats.total_messages}</b> — всего сообщ. за период",
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def _format_replies_stats(stats: RepliesStats) -> str:
        """Форматирует статистику ответов"""
        if stats.total_count == 0:
            return "Из них всего <b>0</b> ответов"

        lines = [f"Из них всего <b>{stats.total_count}</b> ответов:"]

        if stats.min_time_seconds is not None:
            lines.append(
                f"• <b>{format_seconds(stats.min_time_seconds)}</b> — мин. время ответа"
            )
        if stats.max_time_seconds is not None:
            lines.append(
                f"• <b>{format_seconds(stats.max_time_seconds)}</b> — макс. время ответа"
            )
        if stats.avg_time_seconds is not None:
            lines.append(
                f"• <b>{format_seconds(stats.avg_time_seconds)}</b> — сред. время ответа"
            )
        if stats.median_time_seconds is not None:
            lines.append(
                f"• <b>{format_seconds(stats.median_time_seconds)}</b> — медиан. время ответа"
            )

        return "\n".join(lines)

    @staticmethod
    def _format_breaks_single_day(breaks: List[str]) -> str:
        """Форматирует перерывы для однодневного отчета"""
        if not breaks:
            return "<b>⏸️ Перерывы:</b> отсутствуют"
        return "<b>⏸️ Перерывы:</b>\n" + "\n".join(breaks)

    @staticmethod
    def _format_breaks_multiday(breaks: List[str]) -> str:
        """Форматирует перерывы для многодневного отчета"""
        # Для многодневного отчета breaks содержит уже отформатированную строку
        # из BreakAnalysisService.avg_breaks_time
        if not breaks:
            return "Перерывы: отсутствуют"
        # breaks[0] содержит уже отформатированную строку типа "Перерывы:\n• <b>...</b> — средн.время..."
        return breaks[0] if breaks else "Перерывы: отсутствуют"

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
