from unittest.mock import AsyncMock

import pytest

from models import User
from services.user.user_service import UserService
from usecases.user.get_or_create_user import (
    GetOrCreateUserIfNotExistUserCase,
    UserResult,
)


@pytest.fixture
def mock_user_service() -> AsyncMock:
    return AsyncMock(spec=UserService)


@pytest.fixture
def use_case(mock_user_service: AsyncMock) -> GetOrCreateUserIfNotExistUserCase:
    return GetOrCreateUserIfNotExistUserCase(user_service=mock_user_service)


@pytest.mark.asyncio
async def test_get_or_create_success(
    use_case: GetOrCreateUserIfNotExistUserCase, mock_user_service: AsyncMock
) -> None:
    # Arrange
    tg_id = "123"
    username = "test_user"
    user = User(id=1, tg_id=tg_id, username=username)
    mock_user_service.get_user.return_value = user

    # Act
    result = await use_case.execute(tg_id=tg_id, username=username)

    # Assert
    assert result == UserResult(user=user, is_existed=True)
    mock_user_service.get_user.assert_called_once_with(tg_id=tg_id, username=username)


@pytest.mark.asyncio
async def test_get_or_create_creation(
    use_case: GetOrCreateUserIfNotExistUserCase, mock_user_service: AsyncMock
) -> None:
    # Arrange
    tg_id = "123"
    username = "test_user"
    user = User(id=1, tg_id=tg_id, username=username)
    mock_user_service.get_user.return_value = None
    mock_user_service.create_user.return_value = user

    # Act
    result = await use_case.execute(tg_id=tg_id, username=username)

    # Assert
    assert result == UserResult(user=user, is_existed=False)
    mock_user_service.get_user.assert_called_once()
    mock_user_service.create_user.assert_called_once()


@pytest.mark.asyncio
async def test_get_or_create_validation_error(
    use_case: GetOrCreateUserIfNotExistUserCase,
) -> None:
    # Act & Assert
    with pytest.raises(ValueError, match="Either tg_id or username must be provided"):
        await use_case.execute(tg_id=None, username=None)
