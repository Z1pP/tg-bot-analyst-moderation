"""Тесты для HasTrackedUsersUseCase."""

from unittest.mock import AsyncMock

import pytest

from repositories.user_tracking_repository import UserTrackingRepository
from usecases.user_tracking.has_tracked_users import HasTrackedUsersUseCase


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=UserTrackingRepository)


@pytest.fixture
def use_case(mock_repo: AsyncMock) -> HasTrackedUsersUseCase:
    return HasTrackedUsersUseCase(user_tracking_repository=mock_repo)


@pytest.mark.asyncio
async def test_has_tracked_users_true(
    use_case: HasTrackedUsersUseCase, mock_repo: AsyncMock
) -> None:
    mock_repo.has_tracked_users.return_value = True
    result = await use_case.execute(admin_tgid="123")
    assert result is True
    mock_repo.has_tracked_users.assert_called_once_with("123")


@pytest.mark.asyncio
async def test_has_tracked_users_false(
    use_case: HasTrackedUsersUseCase, mock_repo: AsyncMock
) -> None:
    mock_repo.has_tracked_users.return_value = False
    result = await use_case.execute(admin_tgid="456")
    assert result is False
    mock_repo.has_tracked_users.assert_called_once_with("456")
