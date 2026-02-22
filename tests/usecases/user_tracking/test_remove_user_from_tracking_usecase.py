"""Тесты для RemoveUserFromTrackingUseCase."""

from unittest.mock import AsyncMock

import pytest

from constants.enums import UserRole
from dto import RemoveUserTrackingDTO
from models import User
from repositories.user_tracking_repository import UserTrackingRepository
from services import AdminActionLogService, UserService
from usecases.user_tracking.remove_user_from_tracking import (
    RemoveUserFromTrackingUseCase,
)


@pytest.fixture
def mock_user_service() -> AsyncMock:
    return AsyncMock(spec=UserService)


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=UserTrackingRepository)


@pytest.fixture
def mock_admin_log() -> AsyncMock:
    return AsyncMock(spec=AdminActionLogService)


@pytest.fixture
def use_case(
    mock_user_service: AsyncMock,
    mock_repo: AsyncMock,
    mock_admin_log: AsyncMock,
) -> RemoveUserFromTrackingUseCase:
    return RemoveUserFromTrackingUseCase(
        user_tracking_repository=mock_repo,
        user_service=mock_user_service,
        admin_action_log_service=mock_admin_log,
    )


@pytest.mark.asyncio
async def test_remove_user_from_tracking_success(
    use_case: RemoveUserFromTrackingUseCase,
    mock_user_service: AsyncMock,
    mock_repo: AsyncMock,
    mock_admin_log: AsyncMock,
) -> None:
    admin = User(id=2, tg_id="a1", username="admin", role=UserRole.ADMIN)
    user = User(id=1, tg_id="u1", username="user", role=UserRole.USER)
    mock_user_service.get_user.side_effect = [admin, user]

    dto = RemoveUserTrackingDTO(admin_tgid="a1", user_tgid="u1")
    result = await use_case.execute(dto)

    assert result is True
    mock_repo.remove_user_from_tracking.assert_called_once_with(admin_id=2, user_id=1)
    mock_admin_log.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_remove_user_from_tracking_admin_not_found(
    use_case: RemoveUserFromTrackingUseCase, mock_user_service: AsyncMock
) -> None:
    mock_user_service.get_user.return_value = None
    dto = RemoveUserTrackingDTO(admin_tgid="unknown", user_tgid="u1")
    result = await use_case.execute(dto)
    assert result is False


@pytest.mark.asyncio
async def test_remove_user_from_tracking_user_not_found(
    use_case: RemoveUserFromTrackingUseCase, mock_user_service: AsyncMock
) -> None:
    admin = User(id=2, tg_id="a1", username="a1", role=UserRole.ADMIN)
    mock_user_service.get_user.side_effect = [admin, None]
    dto = RemoveUserTrackingDTO(admin_tgid="a1", user_tgid="unknown")
    result = await use_case.execute(dto)
    assert result is False
