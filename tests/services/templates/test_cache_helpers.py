"""Характеризующие тесты invalidate_category_pages."""

from unittest.mock import AsyncMock, call

import pytest

from services.caching import ICache
from services.templates.cache_helpers import (
    CATEGORY_CACHE_PAGES,
    invalidate_category_pages,
)


@pytest.fixture
def mock_cache() -> AsyncMock:
    return AsyncMock(spec=ICache)


@pytest.mark.asyncio
async def test_invalidate_category_pages_deletes_all_pages(
    mock_cache: AsyncMock,
) -> None:
    """Удаляются ключи страниц 1..CATEGORY_CACHE_PAGES указанной категории."""
    # Act
    result = await invalidate_category_pages(mock_cache, category_id=3)

    # Assert
    assert result is None
    expected = [
        call(f"tpl:cat:3:page:{page}")
        for page in range(1, CATEGORY_CACHE_PAGES + 1)
    ]
    assert mock_cache.delete.await_args_list == expected


@pytest.mark.asyncio
async def test_invalidate_category_pages_uses_given_category(
    mock_cache: AsyncMock,
) -> None:
    """Ключи содержат переданный category_id, а не фиксированный."""
    # Act
    await invalidate_category_pages(mock_cache, category_id=77)

    # Assert
    deleted_keys = [c.args[0] for c in mock_cache.delete.await_args_list]
    assert deleted_keys[0] == "tpl:cat:77:page:1"
    assert deleted_keys[-1] == f"tpl:cat:77:page:{CATEGORY_CACHE_PAGES}"
    assert mock_cache.delete.await_count == CATEGORY_CACHE_PAGES