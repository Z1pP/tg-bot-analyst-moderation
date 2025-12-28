from typing import List

from constants import MAX_MSG_LENGTH
from dto.report import (
    RepliesStats,
    SingleUserDayStats,
    SingleUserMultiDayStats,
    SingleUserReportResultDTO,
)
from utils.formatter import format_seconds, format_selected_period


class SingleUserReportPresenter:
    """Класс для форматирования данных отчета по пользователю в HTML строки"""

    @staticmethod
    def format_report(result: SingleUserReportResultDTO) -> List[str]:
        """
        Форматирует SingleUserReportResultDTO в список HTML строк для отправки.

        Args:
            result: DTO с данными отчета

        Returns:
            Список строк отчета (может быть разбит на части)
        """
        if result.error_message:
            period_str = format_selected_period(
                start_date=result.start_date, end_date=result.end_date
            )
            header = f"<b>📈 Отчёт: @{result.username} за {period_str}</b>\n\n"
            return [f"{header}{result.error_message}"]

        period_str = format_selected_period(
            start_date=result.start_date, end_date=result.end_date
        )
        period_prefix = "период " if not result.is_single_day else ""

        header = f"<b>📈 Отчёт: @{result.username} за {period_prefix}{period_str}</b>\n"

        # Проверяем наличие данных
        if not result.day_stats and not result.multi_day_stats:
            no_data_text = "день" if result.is_single_day else "период"
            return [f"\n{header}⚠️ Нет данных за указанный {no_data_text}."]

        report_parts = [header]

        # Добавляем статистику
        if result.is_single_day and result.day_stats:
            report_parts.append(
                SingleUserReportPresenter._format_day_stats(result.day_stats)
            )
        elif not result.is_single_day and result.multi_day_stats:
            report_parts.append(
                SingleUserReportPresenter._format_multi_day_stats(
                    result.multi_day_stats
                )
            )

        # Добавляем статистику ответов
        report_parts.append(
            SingleUserReportPresenter._format_replies_stats(result.replies_stats)
        )

        # Добавляем перерывы
        report_parts.append(
            SingleUserReportPresenter._format_breaks(
                result.breaks, result.is_single_day
            )
        )

        full_report = "\n".join(filter(None, report_parts))

        return SingleUserReportPresenter._split_report(full_report)

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
                f"• <b>{stats.warns_count}</b> - выдано предупреждений",
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
                f"• <b>{stats.warns_count}</b> - выдано предупреждений",
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
            breaks_text = (
                "<b>⏸️ Перерывы:</b>\n"
                + "\n".join(breaks)
                + "\n\n❗Чтобы получить детализацию перерывов по датам, нажмите "
                "соответствующую кнопку"
            )
            return breaks_text

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
        content_parts = parts[1:]

        result = [title]
        current_part = ""

        for part in content_parts:
            if len(current_part) + len(part) + 2 > MAX_MSG_LENGTH:
                if current_part:
                    result.append(current_part)
                current_part = part
            else:
                current_part = f"{current_part}\n\n{part}" if current_part else part

        if current_part:
            result.append(current_part)

        return result
