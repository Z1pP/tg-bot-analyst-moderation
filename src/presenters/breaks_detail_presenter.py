from typing import List

from constants import MAX_MSG_LENGTH
from dto.report import BreaksDetailReportDTO, BreaksDetailUserDTO
from utils.formatter import format_seconds


class BreaksDetailPresenter:
    """Форматирует детализацию перерывов в текст отчета."""

    @staticmethod
    def format_report(result: BreaksDetailReportDTO) -> List[str]:
        """Форматирует отчет по детализации перерывов."""
        if result.error_message:
            return [result.error_message]

        if not result.users:
            return ["⚠️ Нет данных для детализации за указанный период"]

        user_reports = [
            BreaksDetailPresenter._format_user_report(user, result.period)
            for user in result.users
        ]
        full_report = "\n\n".join(user_reports)
        return BreaksDetailPresenter._split_report(full_report)

    @staticmethod
    def _format_user_report(user: BreaksDetailUserDTO, period: str) -> str:
        """Форматирует отчет одного пользователя."""
        header = f"📊 Детализация перерывов: @{user.username} за период {period}"

        if not user.has_activity or not user.days:
            return f"{header}\n\n⏸️ Перерывы отсутствуют"

        day_blocks = []
        for day in user.days:
            day_lines = [
                f"📅{day.date.strftime('%d.%m.%Y')}",
                f"{format_seconds(day.total_break_seconds)} - общее время перерыва за день",
            ]
            day_lines.extend(
                [
                    (
                        f"• {interval.start_time}-{interval.end_time} - "
                        f"{interval.duration_minutes} мин."
                    )
                    for interval in day.intervals
                ]
            )
            day_blocks.append("\n".join(day_lines))

        return f"{header}\n\n" + "\n\n".join(day_blocks)

    @staticmethod
    def _split_report(report: str) -> List[str]:
        """Разделяет отчет на части по лимиту длины."""
        if len(report) <= MAX_MSG_LENGTH:
            return [report]

        parts = report.split("\n\n")
        result = []
        current_part = ""

        for part in parts:
            if len(current_part) + len(part) + 2 > MAX_MSG_LENGTH:
                if current_part:
                    result.append(current_part)
                current_part = part
            else:
                current_part = f"{current_part}\n\n{part}" if current_part else part

        if current_part:
            result.append(current_part)

        return result
