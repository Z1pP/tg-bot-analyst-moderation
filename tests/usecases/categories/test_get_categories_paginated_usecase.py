"""Тесты для GetCategoriesPaginatedUseCase."""

from unittest.mock import AsyncMock

import pytest

from dto import GetCategoriesPaginatedDTO
from models import TemplateCategory
from services.categories.category_service import CategoryService
from usecases.categories.get_categories_paginated import GetCategoriesPaginatedUseCase


@pytest.fixture
def mock_category_service() -> AsyncMock:
    return AsyncMock(spec=CategoryService)


@pytest.fixture
def use_case(mock_category_service: AsyncMock) -> GetCategoriesPaginatedUseCase:
    return GetCategoriesPaginatedUseCase(category_service=mock_category_service)


@pytest.mark.asyncio
async def test_get_categories_paginated(
    use_case: GetCategoriesPaginatedUseCase,
    mock_category_service: AsyncMock,
) -> None:
    categories = [
        TemplateCategory(id=1, name="A", sort_order=0),
        TemplateCategory(id=2, name="B", sort_order=1),
    ]
    mock_category_service.get_categories_paginated.return_value = categories
    mock_category_service.get_categories_count.return_value = 10

    dto = GetCategoriesPaginatedDTO(limit=2, offset=0)
    result_list, total = await use_case.execute(dto)

    assert result_list == categories
    assert total == 10
    mock_category_service.get_categories_paginated.assert_called_once_with(
        limit=2, offset=0
    )
    mock_category_service.get_categories_count.assert_called_once()


@pytest.mark.asyncio
async def test_get_categories_paginated_empty(
    use_case: GetCategoriesPaginatedUseCase,
    mock_category_service: AsyncMock,
) -> None:
    mock_category_service.get_categories_paginated.return_value = []
    mock_category_service.get_categories_count.return_value = 0
    dto = GetCategoriesPaginatedDTO(limit=5, offset=0)
    result_list, total = await use_case.execute(dto)
    assert result_list == []
    assert total == 0
