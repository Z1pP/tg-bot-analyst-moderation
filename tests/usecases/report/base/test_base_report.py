"""Тесты хелперов и расчётов BaseReportUseCase (report/base.py)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from dto.report import SingleUserDayStats, SingleUserMultiDayStats
from usecases.report.user.get_single_user_report import GetSingleUserReportUseCase


@pytest.fixture
def usecase() -> GetSingleUserReportUseCase:
    """Конкретная реализация BaseReportUseCase с моками для вызова хелперов."""
    return GetSingleUserReportUseCase(
        msg_reply_repository=AsyncMock(),
        message_repository=AsyncMock(),
        user_repository=AsyncMock(),
        reaction_repository=AsyncMock(),
        chat_repository=AsyncMock(),
        punishment_repository=AsyncMock(),
        admin_action_log_service=AsyncMock(),
    )


def test_split_report_short_returns_one_part(
    usecase: GetSingleUserReportUseCase,
) -> None:
    """Короткий отчёт возвращается одним куском."""
    report = "Короткий отчёт"
    result = usecase._split_report(report)
    assert result == [report]


def test_split_report_long_splits_by_double_newline(
    usecase: GetSingleUserReportUseCase,
) -> None:
    """Длинный отчёт разбивается по \\n\\n, первый элемент — заголовок."""
    title = "Заголовок"
    part1 = "A" * 3000
    part2 = "B" * 3000
    report = f"{title}\n\n{part1}\n\n{part2}"
    result = usecase._split_report(report)
    assert result[0] == title
    assert len(result) >= 2
    assert part1 in "".join(result)
    assert part2 in "".join(result)


def test_get_avg_time_first_items_empty_returns_empty(
    usecase: GetSingleUserReportUseCase,
) -> None:
    """Пустой список сообщений — пустая строка."""
    assert usecase._get_avg_time_first_items([]) == ""


def test_get_avg_time_first_items_single_day(
    usecase: GetSingleUserReportUseCase,
) -> None:
    """Один день — время первого элемента в формате HH:MM."""
    dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    msg = type("Msg", (), {"created_at": dt})()
    result = usecase._get_avg_time_first_items([msg])
    assert result == "10:30"


def test_calculate_replies_stats_empty(usecase: GetSingleUserReportUseCase) -> None:
    """Пустой список ответов — нулевая статистика."""
    stats = usecase._calculate_replies_stats([])
    assert stats.total_count == 0
    assert stats.min_time_seconds is None
    assert stats.avg_time_seconds is None


def test_calculate_replies_stats_with_data(
    usecase: GetSingleUserReportUseCase,
) -> None:
    """Непустые ответы — считаются min/max/avg/median."""
    replies = [
        type("R", (), {"response_time_seconds": 10})(),
        type("R", (), {"response_time_seconds": 20})(),
        type("R", (), {"response_time_seconds": 30})(),
    ]
    stats = usecase._calculate_replies_stats(replies)
    assert stats.total_count == 3
    assert stats.min_time_seconds == 10
    assert stats.max_time_seconds == 30
    assert stats.avg_time_seconds == 20
    assert stats.median_time_seconds == 20


def test_is_single_day_report_by_period_today(
    usecase: GetSingleUserReportUseCase,
) -> None:
    """Период 'За сегодня' — однодневный отчёт."""
    start = datetime(2025, 1, 1, 9, 0)
    end = datetime(2025, 1, 1, 18, 0)
    assert usecase._is_single_day_report("За сегодня", start, end) is True


def test_is_single_day_report_by_period_yesterday(
    usecase: GetSingleUserReportUseCase,
) -> None:
    """Период 'За вчера' — однодневный отчёт."""
    start = datetime(2025, 1, 1, 0, 0)
    end = datetime(2025, 1, 1, 23, 59)
    assert usecase._is_single_day_report("За вчера", start, end) is True


def test_is_single_day_report_by_dates_one_day(
    usecase: GetSingleUserReportUseCase,
) -> None:
    """Один календарный день (selected_period=None) — однодневный."""
    start = datetime(2025, 1, 1, 9, 0)
    end = datetime(2025, 1, 1, 18, 0)
    assert usecase._is_single_day_report(None, start, end) is True


def test_is_single_day_report_multi_day(
    usecase: GetSingleUserReportUseCase,
) -> None:
    """Несколько дней — не однодневный."""
    start = datetime(2025, 1, 1, 0, 0)
    end = datetime(2025, 1, 5, 23, 59)
    assert usecase._is_single_day_report(None, start, end) is False


def test_format_selected_period(usecase: GetSingleUserReportUseCase) -> None:
    """Форматирование периода в читаемый вид."""
    start = datetime(2025, 1, 15, 0, 0)
    end = datetime(2025, 1, 15, 23, 59)
    text = usecase._format_selected_period(start, end)
    assert "15" in text
    assert "янв" in text or "янв." in text


def test_avg_messages_per_hour_zero_work_hours(
    usecase: GetSingleUserReportUseCase,
) -> None:
    """Нулевые рабочие часы — возвращается 1 (защита от деления на ноль)."""
    start = datetime(2025, 1, 1, 9, 0)
    end = datetime(2025, 1, 1, 9, 0)
    result = usecase._avg_messages_per_hour(10, start, end)
    assert result == 1


def test_avg_message_per_day(usecase: GetSingleUserReportUseCase) -> None:
    """Среднее сообщений в день за несколько дней."""
    start = datetime(2025, 1, 1, 0, 0)
    end = datetime(2025, 1, 5, 0, 0)
    result = usecase._avg_message_per_day(10, start, end)
    assert result == 2.5


def test_calculate_day_stats_empty_returns_none(
    usecase: GetSingleUserReportUseCase,
) -> None:
    """Нет сообщений, реакций и наказаний — None."""
    start = datetime(2025, 1, 1, 9, 0)
    end = datetime(2025, 1, 1, 18, 0)
    result = usecase._calculate_day_stats([], [], start, end)
    assert result is None


def test_calculate_day_stats_with_messages(
    usecase: GetSingleUserReportUseCase,
) -> None:
    """Сообщения есть — возвращается SingleUserDayStats."""
    start = datetime(2025, 1, 1, 9, 0, tzinfo=timezone.utc)
    end = datetime(2025, 1, 1, 18, 0, tzinfo=timezone.utc)

    class Msg:
        def __init__(self, created_at: datetime) -> None:
            self.created_at = created_at

    msg1 = Msg(datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc))
    msg2 = Msg(datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc))
    result = usecase._calculate_day_stats(
        [msg1, msg2], [], start, end, warns_count=0, bans_count=0
    )
    assert isinstance(result, SingleUserDayStats)
    assert result.total_messages == 2
    assert result.first_message_time is not None
    assert result.last_message_time is not None


def test_calculate_multi_day_stats_empty_returns_none(
    usecase: GetSingleUserReportUseCase,
) -> None:
    """Нет данных — None."""
    start = datetime(2025, 1, 1, 9, 0)
    end = datetime(2025, 1, 5, 18, 0)
    result = usecase._calculate_multi_day_stats([], [], start, end)
    assert result is None


def test_calculate_multi_day_stats_with_messages(
    usecase: GetSingleUserReportUseCase,
) -> None:
    """Есть сообщения — SingleUserMultiDayStats."""
    start = datetime(2025, 1, 1, 9, 0, tzinfo=timezone.utc)
    end = datetime(2025, 1, 3, 18, 0, tzinfo=timezone.utc)

    class Msg:
        def __init__(self, created_at: datetime) -> None:
            self.created_at = created_at

    msg = Msg(datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc))
    result = usecase._calculate_multi_day_stats(
        [msg], [], start, end, warns_count=1, bans_count=0
    )
    assert isinstance(result, SingleUserMultiDayStats)
    assert result.total_messages == 1
    assert result.warns_count == 1
