"""Тесты для utils/moderation.py."""

from unittest.mock import AsyncMock

import pytest

from utils.moderation import (
    ViolatorData,
    extract_violator_data_from_state,
    format_violator_display,
    format_violator_mention_suffix,
)


def test_format_violator_display_with_username() -> None:
    """С username возвращается @username."""
    assert format_violator_display("john", "123") == "@john"


def test_format_violator_display_without_username() -> None:
    """Без username возвращается ID:tg_id."""
    assert format_violator_display(None, "456") == "ID:456"


def test_format_violator_display_empty_username() -> None:
    """Пустая строка как username трактуется как отсутствие — ID:tg_id."""
    assert format_violator_display("", "789") == "ID:789"


def test_format_violator_display_hidden() -> None:
    """Служебное значение hidden даёт ID:tg_id."""
    assert format_violator_display("hidden", "111") == "ID:111"


def test_format_violator_mention_suffix_with_username() -> None:
    """С username возвращается username (без @)."""
    assert format_violator_mention_suffix("john", "123") == "john"


def test_format_violator_mention_suffix_without_username() -> None:
    """Без username возвращается ID:tg_id."""
    assert format_violator_mention_suffix(None, "456") == "ID:456"


def test_format_violator_mention_suffix_hidden() -> None:
    """hidden даёт ID:tg_id."""
    assert format_violator_mention_suffix("hidden", "789") == "ID:789"


@pytest.mark.asyncio
async def test_extract_violator_data_from_state() -> None:
    """Извлечение данных нарушителя из FSM state."""
    state = AsyncMock()
    state.get_data = AsyncMock(
        return_value={"id": 1, "username": "violator", "tg_id": 999}
    )
    result = await extract_violator_data_from_state(state)
    assert result == ViolatorData(id=1, username="violator", tg_id=999)
    state.get_data.assert_called_once()


@pytest.mark.asyncio
async def test_extract_violator_data_from_state_partial() -> None:
    """get_data может вернуть не все ключи — используются значения по умолчанию."""
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    result = await extract_violator_data_from_state(state)
    assert result.id is None
    assert result.username is None
    assert result.tg_id is None
