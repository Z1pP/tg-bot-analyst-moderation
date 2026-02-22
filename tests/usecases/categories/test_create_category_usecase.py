"""Тесты для CreateCategoryUseCase."""

from unittest.mock import AsyncMock

import pytest

from dto import CreateCategoryDTO
from exceptions.category import CategoryAlreadyExists
from models import TemplateCategory
from services import AdminActionLogService, CategoryService
from usecases.categories.create_category import CreateCategoryUseCase


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
) -> CreateCategoryUseCase:
    return CreateCategoryUseCase(
        category_service=mock_category_service,
        admin_action_log_service=mock_admin_log,
    )


@pytest.mark.asyncio
async def test_create_category_success(
    use_case: CreateCategoryUseCase,
    mock_category_service: AsyncMock,
    mock_admin_log: AsyncMock,
) -> None:
    created = TemplateCategory(id=1, name="NewCat", sort_order=0)
    mock_category_service.get_categories.return_value = []
    mock_category_service.create_category.return_value = created

    dto = CreateCategoryDTO(name="NewCat")
    result = await use_case.execute(dto, admin_tg_id="123")

    assert result.id == 1
    assert result.name == "NewCat"
    mock_category_service.create_category.assert_called_once_with(name="NewCat")
    mock_admin_log.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_create_category_already_exists(
    use_case: CreateCategoryUseCase, mock_category_service: AsyncMock
) -> None:
    existing = TemplateCategory(id=1, name="Existing", sort_order=0)
    mock_category_service.get_categories.return_value = [existing]

    dto = CreateCategoryDTO(name="Existing")
    with pytest.raises(CategoryAlreadyExists) as exc_info:
        await use_case.execute(dto)
    assert exc_info.value.name == "Existing"
    mock_category_service.create_category.assert_not_called()
