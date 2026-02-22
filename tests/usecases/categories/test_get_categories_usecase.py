"""Тесты для GetCategoriesUseCase."""

from unittest.mock import AsyncMock

import pytest

from models import TemplateCategory
from services.categories.category_service import CategoryService
from usecases.categories.get_categories import GetCategoriesUseCase


@pytest.fixture
def mock_category_service() -> AsyncMock:
    return AsyncMock(spec=CategoryService)


@pytest.fixture
def use_case(mock_category_service: AsyncMock) -> GetCategoriesUseCase:
    return GetCategoriesUseCase(category_service=mock_category_service)


@pytest.mark.asyncio
async def test_get_categories_returns_list(
    use_case: GetCategoriesUseCase, mock_category_service: AsyncMock
) -> None:
    categories = [
        TemplateCategory(id=1, name="Cat1", sort_order=0),
        TemplateCategory(id=2, name="Cat2", sort_order=1),
    ]
    mock_category_service.get_categories.return_value = categories
    result = await use_case.execute()
    assert result == categories
    mock_category_service.get_categories.assert_called_once()


@pytest.mark.asyncio
async def test_get_categories_empty(
    use_case: GetCategoriesUseCase, mock_category_service: AsyncMock
) -> None:
    mock_category_service.get_categories.return_value = []
    result = await use_case.execute()
    assert result == []
