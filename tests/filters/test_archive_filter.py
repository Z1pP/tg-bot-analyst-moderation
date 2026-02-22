"""Тесты для filters/archive_filter.py."""

from unittest.mock import MagicMock

import pytest
from aiogram.types import Message

from filters.archive_filter import HASH_PATTERN, ArchiveHashFilter


@pytest.mark.asyncio
async def test_archive_hash_filter_has_hash_in_text() -> None:
    """ArchiveHashFilter возвращает True, если в тексте есть ARCHIVE-{hash}."""
    flt = ArchiveHashFilter()
    msg = Message.model_construct(
        message_id=1,
        date=MagicMock(),
        chat=MagicMock(),
        text="Привязка: ARCHIVE-abc123XYZ",
    )

    result = await flt(msg)

    assert result is True


@pytest.mark.asyncio
async def test_archive_hash_filter_no_hash_returns_false() -> None:
    """ArchiveHashFilter возвращает False, если hash нет."""
    flt = ArchiveHashFilter()
    msg = Message.model_construct(
        message_id=1,
        date=MagicMock(),
        chat=MagicMock(),
        text="Обычное сообщение",
    )

    result = await flt(msg)

    assert result is False


@pytest.mark.asyncio
async def test_archive_hash_filter_empty_text_returns_false() -> None:
    """ArchiveHashFilter возвращает False при пустом text и caption."""
    flt = ArchiveHashFilter()
    msg = Message.model_construct(
        message_id=1,
        date=MagicMock(),
        chat=MagicMock(),
        text=None,
        caption=None,
    )

    result = await flt(msg)

    assert result is False


@pytest.mark.asyncio
async def test_archive_hash_filter_hash_in_caption() -> None:
    """ArchiveHashFilter проверяет caption, если text пустой."""
    flt = ArchiveHashFilter()
    msg = Message.model_construct(
        message_id=1,
        date=MagicMock(),
        chat=MagicMock(),
        text=None,
        caption="ARCHIVE-hash_from_caption",
    )

    result = await flt(msg)

    assert result is True


def test_hash_pattern_constant() -> None:
    """HASH_PATTERN находит ARCHIVE- и буквенно-цифровой hash."""
    assert HASH_PATTERN.search("ARCHIVE-abc123")
    assert HASH_PATTERN.search("text ARCHIVE-XyZ_9- end")
    assert not HASH_PATTERN.search("no hash here")
