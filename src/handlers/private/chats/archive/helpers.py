"""Shared helpers for archive handlers."""

from __future__ import annotations

from typing import Optional, Tuple

from models.report_schedule import ReportSchedule
from services.time_service import TimeZoneService


def build_schedule_info(schedule: Optional[ReportSchedule]) -> Tuple[str, bool]:
    """Build schedule status text and enabled flag.

    Args:
        schedule: Existing schedule or None.

    Returns:
        Tuple with formatted schedule info text and enabled flag.
    """
    if schedule:
        enabled = schedule.enabled
        enabled_text = "🟢 Включена" if enabled else "🔴 Выключена"
        schedule_info = f"📧 Рассылка: {enabled_text}\n"

        if enabled and schedule.next_run_at:
            next_run_local = TimeZoneService.convert_to_local_time(schedule.next_run_at)
            next_run_str = next_run_local.strftime("%d.%m.%Y в %H:%M")
            schedule_info += f"🕐 Следующая рассылка: {next_run_str}"
        elif enabled:
            schedule_info += "🕐 Следующая рассылка: не запланирована"
    else:
        enabled = False
        schedule_info = "📧 Рассылка: 🔴 Выключена\n🕐 Следующая рассылка: не настроена"

    return schedule_info, enabled
