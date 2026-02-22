"""Тесты для AddUserToTrackingUseCase."""

from unittest.mock import AsyncMock

import pytest

from constants.enums import UserRole
from dto import UserTrackingDTO
from models import User
from repositories.user_tracking_repository import UserTrackingRepository
from services import AdminActionLogService, UserService
from usecases.user_tracking.add_user_to_tracking import (
    AddUserToTrackingUseCase,
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
) -> AddUserToTrackingUseCase:
    return AddUserToTrackingUseCase(
        user_service=mock_user_service,
        user_tracking_repository=mock_repo,
        admin_action_log_service=mock_admin_log,
    )


@pytest.mark.asyncio
async def test_add_user_to_tracking_success(
    use_case: AddUserToTrackingUseCase,
    mock_user_service: AsyncMock,
    mock_repo: AsyncMock,
    mock_admin_log: AsyncMock,
) -> None:
    user = User(id=1, tg_id="u1", username="user1", role=UserRole.USER)
    admin = User(id=2, tg_id="admin1", username="admin1", role=UserRole.ADMIN)
    mock_user_service.get_user.side_effect = [user, admin]
    mock_repo.get_tracked_users_by_admin.return_value = []

    dto = UserTrackingDTO(admin_tgid="admin1", user_tgid="u1")
    result = await use_case.execute(dto)

    assert result.success is True
    assert result.user_id == 1
    mock_repo.add_user_to_tracking.assert_called_once_with(admin_id=2, user_id=1)
    mock_admin_log.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_add_user_to_tracking_user_not_found(
    use_case: AddUserToTrackingUseCase, mock_user_service: AsyncMock
) -> None:
    mock_user_service.get_user.return_value = None
    dto = UserTrackingDTO(admin_tgid="admin1", user_tgid="unknown")
    result = await use_case.execute(dto)
    assert result.success is False
    assert result.message is not None
    mock_user_service.get_user.assert_called()


@pytest.mark.asyncio
async def test_add_user_to_tracking_admin_not_found(
    use_case: AddUserToTrackingUseCase, mock_user_service: AsyncMock
) -> None:
    user = User(id=1, tg_id="u1", username="u1", role=UserRole.USER)
    mock_user_service.get_user.side_effect = [user, None]
    dto = UserTrackingDTO(admin_tgid="unknown", user_tgid="u1")
    result = await use_case.execute(dto)
    assert result.success is False


@pytest.mark.asyncio
async def test_add_user_to_tracking_already_tracked(
    use_case: AddUserToTrackingUseCase,
    mock_user_service: AsyncMock,
    mock_repo: AsyncMock,
) -> None:
    user = User(id=1, tg_id="u1", username="u1", role=UserRole.USER)
    admin = User(id=2, tg_id="a1", username="a1", role=UserRole.ADMIN)
    mock_user_service.get_user.side_effect = [user, admin]
    mock_repo.get_tracked_users_by_admin.return_value = [user]

    dto = UserTrackingDTO(admin_tgid="a1", user_tgid="u1")
    result = await use_case.execute(dto)

    assert result.success is False
    assert result.user_id == 1
    mock_repo.add_user_to_tracking.assert_not_called()
