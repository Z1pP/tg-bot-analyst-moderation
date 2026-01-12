from unittest.mock import AsyncMock

import pytest

from constants.enums import UserRole
from models import User
from repositories.user_repository import UserRepository
from services import AdminActionLogService
from services.caching import ICache
from usecases.user.update_user_role import UpdateUserRoleUseCase


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def mock_cache() -> AsyncMock:
    return AsyncMock(spec=ICache)


@pytest.fixture
def mock_admin_action_log_service() -> AsyncMock:
    return AsyncMock(spec=AdminActionLogService)


@pytest.fixture
def use_case(
    mock_user_repo: AsyncMock,
    mock_cache: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
) -> UpdateUserRoleUseCase:
    return UpdateUserRoleUseCase(
        user_repository=mock_user_repo,
        cache=mock_cache,
        admin_action_log_service=mock_admin_action_log_service,
    )


@pytest.mark.asyncio
async def test_update_user_role_success(
    use_case: UpdateUserRoleUseCase,
    mock_user_repo: AsyncMock,
    mock_cache: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
) -> None:
    # Arrange
    user_id = 1
    admin_tg_id = "admin123"
    old_role = UserRole.USER
    new_role = UserRole.MODERATOR
    user = User(id=user_id, tg_id="123", username="test_user", role=old_role)
    updated_user = User(id=user_id, tg_id="123", username="test_user", role=new_role)

    mock_user_repo.get_user_by_id.return_value = user
    mock_user_repo.update_user_role.return_value = updated_user

    # Act
    result = await use_case.execute(
        user_id=user_id, new_role=new_role, admin_tg_id=admin_tg_id
    )

    # Assert
    assert result == updated_user
    mock_user_repo.get_user_by_id.assert_called_once_with(user_id=user_id)
    mock_user_repo.update_user_role.assert_called_once_with(
        user_id=user_id, new_role=new_role
    )

    # Check cache interaction
    assert mock_cache.delete.call_count >= 2
    assert mock_cache.set.call_count >= 2

    # Check admin action logging
    mock_admin_action_log_service.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_role_not_found(
    use_case: UpdateUserRoleUseCase,
    mock_user_repo: AsyncMock,
) -> None:
    # Arrange
    mock_user_repo.get_user_by_id.return_value = None

    # Act
    result = await use_case.execute(
        user_id=999, new_role=UserRole.MODERATOR, admin_tg_id="admin"
    )

    # Assert
    assert result is None
    mock_user_repo.get_user_by_id.assert_called_once()
    mock_user_repo.update_user_role.assert_not_called()
