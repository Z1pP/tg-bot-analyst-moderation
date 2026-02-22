"""Тесты для CategoryService."""

from unittest.mock import AsyncMock

import pytest

from models import TemplateCategory
from repositories.categories_repository import TemplateCategoryRepository
from services.caching.base import ICache
from services.categories.category_service import CategoryService


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=TemplateCategoryRepository)


@pytest.fixture
def mock_cache() -> AsyncMock:
    return AsyncMock(spec=ICache)


@pytest.fixture
def service(
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> CategoryService:
    return CategoryService(
        category_repository=mock_repo,
        cache=mock_cache,
    )


@pytest.mark.asyncio
async def test_get_categories_cache_hit(
    service: CategoryService, mock_cache: AsyncMock, mock_repo: AsyncMock
) -> None:
    """При попадании в кэш репозиторий не вызывается."""
    categories = [TemplateCategory(id=1, name="C1", sort_order=0)]
    mock_cache.get.return_value = categories
    result = await service.get_categories()
    assert result == categories
    mock_cache.get.assert_called_once()
    mock_repo.get_all_categories.assert_not_called()


@pytest.mark.asyncio
async def test_get_categories_cache_miss(
    service: CategoryService, mock_cache: AsyncMock, mock_repo: AsyncMock
) -> None:
    """При промахе кэша данные берутся из репозитория и кэшируются."""
    categories = [TemplateCategory(id=1, name="C1", sort_order=0)]
    mock_cache.get.return_value = None
    mock_repo.get_all_categories.return_value = categories
    result = await service.get_categories()
    assert result == categories
    mock_repo.get_all_categories.assert_called_once()
    mock_cache.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_category_by_id(
    service: CategoryService, mock_repo: AsyncMock
) -> None:
    cat = TemplateCategory(id=1, name="Cat", sort_order=0)
    mock_repo.get_category_by_id.return_value = cat
    result = await service.get_category_by_id(1)
    assert result == cat
    mock_repo.get_category_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_create_category(
    service: CategoryService, mock_repo: AsyncMock, mock_cache: AsyncMock
) -> None:
    created = TemplateCategory(id=1, name="New", sort_order=0)
    mock_repo.create_category.return_value = created
    result = await service.create_category("New")
    assert result == created
    mock_repo.create_category.assert_called_once_with(name="New")
    mock_cache.delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_category(
    service: CategoryService, mock_repo: AsyncMock, mock_cache: AsyncMock
) -> None:
    await service.delete_category(1)
    mock_repo.delete_category.assert_called_once_with(category_id=1)
    mock_cache.delete.assert_called_once()


@pytest.mark.asyncio
async def test_get_categories_paginated(
    service: CategoryService, mock_repo: AsyncMock
) -> None:
    categories = [TemplateCategory(id=1, name="A", sort_order=0)]
    mock_repo.get_categories_paginated.return_value = categories
    result = await service.get_categories_paginated(limit=5, offset=0)
    assert result == categories
    mock_repo.get_categories_paginated.assert_called_once_with(limit=5, offset=0)


@pytest.mark.asyncio
async def test_get_categories_count(
    service: CategoryService, mock_repo: AsyncMock
) -> None:
    mock_repo.get_categories_count.return_value = 10
    result = await service.get_categories_count()
    assert result == 10
    mock_repo.get_categories_count.assert_called_once()
