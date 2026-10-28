"""Тесты use cases статистики Mini App."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from dto.stats import ActivityStatsDTO, ModeratorsStatsDTO, StatsSummaryDTO
from services.time_service import TimeZoneService
from usecases.stats import (
    GetActivityStatsUseCase,
    GetModeratorsStatsUseCase,
    GetStatsSummaryUseCase,
)


def _user(user_id: int, tg_id: str, username: str | None) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.tg_id = tg_id
    user.username = username
    return user


@pytest.mark.asyncio
async def test_stats_summary_counts_actions_for_moderators() -> None:
    """Сводка суммирует варны и баны по всем модераторам."""
    user_repo = MagicMock()
    user_repo.get_all_moderators = AsyncMock(return_value=[_user(1, "1", "a")])
    punishment_repo = MagicMock()
    punishment_repo.get_punishment_counts_by_moderator = AsyncMock(
        side_effect=[
            {"warns": 1, "bans": 2},
            {"warns": 10, "bans": 20},
        ]
    )
    usecase = GetStatsSummaryUseCase(
        punishment_repository=punishment_repo,
        user_repository=user_repo,
    )

    result = await usecase.execute()

    assert result == StatsSummaryDTO(
        active_users=1,
        moderation_actions=30,
        today_actions=3,
    )


@pytest.mark.asyncio
async def test_activity_stats_returns_one_entry_per_day(monkeypatch) -> None:
    """Активность возвращает по записи на каждый день периода."""
    fixed_now = datetime(2026, 10, 28, 12, 0)
    monkeypatch.setattr(TimeZoneService, "now", staticmethod(lambda: fixed_now))

    message_repo = MagicMock()
    message_repo.count_messages_by_date_range = AsyncMock(return_value=5)
    punishment_repo = MagicMock()
    punishment_repo.get_daily_punishment_counts = AsyncMock(
        return_value={"2026-10-28": {"warns": 1, "bans": 2}}
    )
    usecase = GetActivityStatsUseCase(
        message_repository=message_repo,
        punishment_repository=punishment_repo,
    )

    result = await usecase.execute(days_count=7)

    assert isinstance(result, ActivityStatsDTO)
    assert result.days == 7
    assert len(result.activity) == 7
    assert result.activity[-1].date == "2026-10-28"
    assert result.activity[-1].messages == 5
    assert result.activity[-1].warns == 1
    assert result.activity[-1].bans == 2


@pytest.mark.asyncio
async def test_activity_stats_falls_back_to_zero_on_errors(monkeypatch) -> None:
    """Ошибки репозиториев не ломают ответ, значения заменяются нулями."""
    fixed_now = datetime(2026, 10, 28, 12, 0)
    monkeypatch.setattr(TimeZoneService, "now", staticmethod(lambda: fixed_now))

    message_repo = MagicMock()
    message_repo.count_messages_by_date_range = AsyncMock(
        side_effect=RuntimeError("db down")
    )
    punishment_repo = MagicMock()
    punishment_repo.get_daily_punishment_counts = AsyncMock(
        side_effect=RuntimeError("db down")
    )
    usecase = GetActivityStatsUseCase(
        message_repository=message_repo,
        punishment_repository=punishment_repo,
    )

    result = await usecase.execute(days_count=7)

    assert all(day.messages == 0 for day in result.activity)
    assert all(day.warns == 0 and day.bans == 0 for day in result.activity)


@pytest.mark.asyncio
async def test_moderators_stats_sorted_by_total() -> None:
    """Разбивка по модераторам сортируется по сумме наказаний."""
    user_repo = MagicMock()
    user_repo.get_all_moderators = AsyncMock(
        return_value=[_user(1, "1", "a"), _user(2, "2", None)]
    )
    punishment_repo = MagicMock()
    punishment_repo.get_punishment_counts_by_moderators = AsyncMock(
        return_value={1: {"warns": 1, "bans": 0}, 2: {"warns": 3, "bans": 4}}
    )
    usecase = GetModeratorsStatsUseCase(
        punishment_repository=punishment_repo,
        user_repository=user_repo,
    )

    result = await usecase.execute(
        period="За сегодня",
        start_date=datetime(2026, 10, 28),
        end_date=datetime(2026, 10, 29),
    )

    assert isinstance(result, ModeratorsStatsDTO)
    assert [item.username for item in result.moderators] == ["ID:2", "a"]
    assert result.moderators[0].total == 7


@pytest.mark.asyncio
async def test_moderators_stats_empty_when_no_moderators() -> None:
    """Без модераторов возвращается пустой список."""
    user_repo = MagicMock()
    user_repo.get_all_moderators = AsyncMock(return_value=[])
    punishment_repo = MagicMock()
    usecase = GetModeratorsStatsUseCase(
        punishment_repository=punishment_repo,
        user_repository=user_repo,
    )

    result = await usecase.execute(
        period="За сегодня",
        start_date=datetime(2026, 10, 28),
        end_date=datetime(2026, 10, 29),
    )

    assert result.moderators == []
    punishment_repo.get_punishment_counts_by_moderators.assert_not_called()