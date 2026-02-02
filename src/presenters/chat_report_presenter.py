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


class ChatReportPresenter:
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
        chat_name = f"{result.chat_title}" if result.chat_title else "чате"

        header = f"📊 Отчёт: {chat_name} за {period_str}\n\n"

        if not result.users_stats:
            return [f"{header}⚠️ Нет активности за указанный период"]

        user_reports = []
        for user_stats in result.users_stats:
            user_report = ChatReportPresenter.format_user_stats(
                user_stats, result.is_single_day
            )
            user_reports.append(user_report)

        report_body = "\n\n".join(user_reports)

        if not result.is_single_day:
            report_body += (
                "\n\n❗️Чтобы получить детализацию перерывов по датам, "
                'нажмите "Заказ детализации перерывов" под сообщением'
            )

        full_report = f"{header}{report_body}"

        return ChatReportPresenter._split_report(full_report)

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
        parts = [f"🙂 @{stats.username}:\n"]

        # 🚫 Модерация - отображаем всегда
        parts.append("🚫 Модерация:")
        if is_single_day and stats.day_stats:
            parts.append(f"• {stats.day_stats.warns_count} - выдано предупреждений")
            parts.append(f"• {stats.day_stats.bans_count} - выдано банов")
        elif not is_single_day and stats.multi_day_stats:
            parts.append(
                f"• {stats.multi_day_stats.warns_count} - всего выдано предупреждений"
            )
            parts.append(f"• {stats.multi_day_stats.bans_count} - всего выдано банов")
        parts.append("")

        # 💬 Сообщения и ответы
        msg_parts = []
        if is_single_day and stats.day_stats:
            msg_parts.append(
                ChatReportPresenter._format_day_message_stats(stats.day_stats)
            )
        elif not is_single_day and stats.multi_day_stats:
            msg_parts.append(
                ChatReportPresenter._format_multi_day_message_stats(
                    stats.multi_day_stats
                )
            )

        replies_text = ChatReportPresenter._format_replies_stats(
            stats.replies_stats, is_single_day
        )
        if replies_text:
            msg_parts.append(replies_text)

        if msg_parts:
            parts.append("💬 Сообщения и ответы:")
            parts.extend(msg_parts)
            parts.append("")

        # ⏸️ Перерывы
        break_parts = []
        if stats.total_break_time:
            break_parts.append(
                f"{stats.total_break_time} - общее время перерыва за период"
            )

        if is_single_day and stats.breaks:
            # Пропускаем первую строку (которая с общим временем), так как мы её уже добавили выше
            break_lines = [
                b for b in stats.breaks if "общее время перерыва" not in b and b.strip()
            ]
            if break_lines:
                break_parts.extend(break_lines)

        if break_parts:
            parts.append("⏸️ Перерывы:")
            parts.extend(break_parts)

        # Удаляем лишнюю пустую строку в конце если она есть
        if parts and not parts[-1]:
            parts.pop()

        return "\n".join(parts)

    @staticmethod
    def _format_day_message_stats(stats: UserDayStats) -> str:
        """Форматирует статистику сообщений за один день"""
        lines = []
        if stats.first_message_time:
            lines.append(f"• {stats.first_message_time.strftime('%H:%M')} - 1-е сообщ.")

        if stats.first_reaction_time:
            lines.append(
                f"• {stats.first_reaction_time.strftime('%H:%M')} - 1-я реакция на сообщ."
            )

        if stats.last_message_time:
            lines.append(
                f"• {stats.last_message_time.strftime('%H:%M')} - последнее сообщ."
            )

        if lines:
            lines.append("")

        lines.append(f"• {stats.total_messages} - всего сообщ.")
        lines.append(f"• {stats.avg_messages_per_hour} - сред. кол-во сообщ./час")

        return "\n".join(lines)

    @staticmethod
    def _format_multi_day_message_stats(stats: UserMultiDayStats) -> str:
        """Форматирует статистику сообщений за несколько дней"""
        lines = []
        if stats.avg_first_message_time:
            lines.append(f"• {stats.avg_first_message_time} - ср. вр. 1-го сообщ.")

        if stats.avg_first_reaction_time:
            lines.append(f"• {stats.avg_first_reaction_time} - ср. вр. 1-й реакции")

        if stats.avg_last_message_time:
            lines.append(f"• {stats.avg_last_message_time} - ср. вр. последнего сообщ.")

        if lines:
            lines.append("")

        lines.append(f"• {stats.total_messages} - всего сообщ. за период")
        lines.append(f"• {stats.avg_messages_per_hour} - ср. кол-во сообщ./час")

        return "\n".join(lines)

    @staticmethod
    def _format_replies_stats(stats: RepliesStats, is_single_day: bool) -> str:
        """Форматирует статистику ответов"""
        if stats.total_count == 0:
            return ""

        prefix = "ср. " if not is_single_day else ""

        lines = [f"Из них {stats.total_count} ответов:"]

        if stats.min_time_seconds is not None:
            lines.append(
                f"• {format_seconds(stats.min_time_seconds)} - {prefix}мин. время отв."
            )

        if stats.max_time_seconds is not None:
            lines.append(
                f"• {format_seconds(stats.max_time_seconds)} - {prefix}макс. время отв."
            )

        if stats.avg_time_seconds is not None:
            lines.append(
                f"• {format_seconds(stats.avg_time_seconds)} - {prefix}сред. время отв."
            )

        if stats.median_time_seconds is not None:
            lines.append(
                f"• {format_seconds(stats.median_time_seconds)} - {prefix}медиан. время отв."
            )

        return "\n".join(lines)

    @staticmethod
    def _split_report(report: str) -> List[str]:
        """
        Разделяет отчет на части по лимиту длины сообщения.
        """
        if len(report) <= MAX_MSG_LENGTH:
            return [report]

        # Упрощенное разбиение для этого презентера
        parts = []
        current_part = ""

        for line in report.split("\n"):
            if len(current_part) + len(line) + 1 > MAX_MSG_LENGTH:
                parts.append(current_part.strip())
                current_part = ""
            current_part += line + "\n"

        if current_part:
            parts.append(current_part.strip())

        return parts
