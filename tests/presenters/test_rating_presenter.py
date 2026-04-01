"""Тесты для RatingPresenter."""

from datetime import datetime, timezone

import pytest

from dto.daily_activity import (
    ChatDailyStatsDTO,
    PopularReactionDTO,
    UserDailyActivityDTO,
    UserReactionActivityDTO,
)
from presenters.rating_presenter import RatingPresenter


@pytest.fixture
def stats_empty() -> ChatDailyStatsDTO:
    start = datetime(2025, 1, 15, 0, 0, tzinfo=timezone.utc)
    return ChatDailyStatsDTO(
        chat_id=1,
        chat_title="",
        top_users=[],
        top_reactors=[],
        popular_reactions=[],
        total_messages=0,
        total_reactions=0,
        active_users_count=0,
        start_date=start,
        end_date=None,
        total_users_count=0,
    )


@pytest.fixture
def stats_with_data() -> ChatDailyStatsDTO:
    start = datetime(2025, 1, 15, 0, 0, tzinfo=timezone.utc)
    return ChatDailyStatsDTO(
        chat_id=1,
        chat_title="Test Chat",
        top_users=[
            UserDailyActivityDTO(user_id=1, username="alice", message_count=10, rank=1),
        ],
        top_reactors=[
            UserReactionActivityDTO(
                user_id=2, username="bob", reaction_count=5, rank=1
            ),
        ],
        popular_reactions=[
            PopularReactionDTO(emoji="👍", count=20, rank=1),
        ],
        total_messages=100,
        total_reactions=50,
        active_users_count=5,
        start_date=start,
        end_date=None,
        total_users_count=10,
    )


def test_format_daily_rating_empty_returns_no_activity(
    stats_empty: ChatDailyStatsDTO,
) -> None:
    """При отсутствии топов возвращается заголовок и NO_ACTIVITY."""
    result = RatingPresenter.format_daily_rating(stats_empty)
    assert "рейтинг" in result.lower() or "rating" in result.lower()
    assert "активност" in result.lower() or "нет" in result.lower()


def test_format_daily_rating_with_data_includes_header_and_sections(
    stats_with_data: ChatDailyStatsDTO,
) -> None:
    """При наличии данных в вывод входят заголовок, топ сообщений и реакций."""
    result = RatingPresenter.format_daily_rating(stats_with_data)
    assert "Test Chat" in result or "чате" in result
    assert "alice" in result or "@alice" in result
    assert "10" in result
    assert "bob" in result or "@bob" in result
    assert "5" in result
    assert "👍" in result
    assert "Вступили" in result


def test_format_daily_rating_no_top_but_membership_shows_stats_and_no_activity() -> (
    None
):
    """Без топа по сообщениям, но с событиями состава — шапка с цифрами и NO_ACTIVITY."""
    start = datetime(2025, 1, 15, 0, 0, tzinfo=timezone.utc)
    stats = ChatDailyStatsDTO(
        chat_id=1,
        chat_title="X",
        top_users=[],
        top_reactors=[],
        popular_reactions=[],
        total_messages=0,
        total_reactions=0,
        active_users_count=0,
        joins_count=3,
        left_count=1,
        removed_count=2,
        start_date=start,
        end_date=None,
        total_users_count=100,
    )
    result = RatingPresenter.format_daily_rating(stats)
    assert "3" in result
    assert "1" in result
    assert "2" in result
    assert "активност" in result.lower() or "нет" in result.lower()
