"""Тесты для DeleteCategoryUseCase."""

from unittest.mock import AsyncMock

import pytest

from exceptions.category import CategoryNotFoundError
from models import TemplateCategory
from services import AdminActionLogService, CategoryService
from usecases.categories.delete_category import DeleteCategoryUseCase


@pytest.fixture
def mock_category_service() -> AsyncMock:
    return AsyncMock(spec=CategoryService)


@pytest.fixture
def mock_admin_log() -> AsyncMock:
    return AsyncMock(spec=AdminActionLogService)


@pytest.fixture
def use_case(
    mock_category_service: AsyncMock,
    mock_admin_log: AsyncMock,
) -> DeleteCategoryUseCase:
    return DeleteCategoryUseCase(
        category_service=mock_category_service,
        admin_action_log_service=mock_admin_log,
    )


@pytest.mark.asyncio
async def test_delete_category_success(
    use_case: DeleteCategoryUseCase,
    mock_category_service: AsyncMock,
    mock_admin_log: AsyncMock,
) -> None:
    category = TemplateCategory(id=1, name="ToDelete", sort_order=0)
    mock_category_service.get_category_by_id.return_value = category

    result = await use_case.execute(category_id=1, admin_tg_id="123")

    assert result is not None
    assert result.id == 1
    assert result.name == "ToDelete"
    mock_category_service.delete_category.assert_called_once_with(1)
    mock_admin_log.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_delete_category_not_found(
    use_case: DeleteCategoryUseCase, mock_category_service: AsyncMock
) -> None:
    mock_category_service.get_category_by_id.return_value = None
    with pytest.raises(CategoryNotFoundError):
        await use_case.execute(category_id=999)
    mock_category_service.delete_category.assert_not_called()
