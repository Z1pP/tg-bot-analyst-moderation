from unittest.mock import AsyncMock

import pytest

from models import User
from repositories.user_repository import UserRepository
from services.caching import ICache
from usecases.user.get_or_create_user import (
    GetOrCreateUserIfNotExistUserCase,
    UserResult,
)


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def mock_cache() -> AsyncMock:
    return AsyncMock(spec=ICache)


@pytest.fixture
def use_case(
    mock_user_repo: AsyncMock, mock_cache: AsyncMock
) -> GetOrCreateUserIfNotExistUserCase:
    return GetOrCreateUserIfNotExistUserCase(
        user_repository=mock_user_repo, cache_service=mock_cache
    )


@pytest.mark.asyncio
async def test_get_or_create_cache_hit(
    use_case: GetOrCreateUserIfNotExistUserCase, mock_cache: AsyncMock
) -> None:
    # Arrange
    tg_id = "123"
    user = User(id=1, tg_id=tg_id)
    mock_cache.get.return_value = user

    # Act
    result = await use_case.execute(tg_id=tg_id)

    # Assert
    assert result == UserResult(user=user, is_existed=True)
    mock_cache.get.assert_called_once_with(key=tg_id)


@pytest.mark.asyncio
async def test_get_or_create_db_hit(
    use_case: GetOrCreateUserIfNotExistUserCase,
    mock_cache: AsyncMock,
    mock_user_repo: AsyncMock,
) -> None:
    # Arrange
    tg_id = "123"
    user = User(id=1, tg_id=tg_id)
    mock_cache.get.return_value = None
    mock_user_repo.get_user_by_tg_id.return_value = user

    # Act
    result = await use_case.execute(tg_id=tg_id)

    # Assert
    assert result == UserResult(user=user, is_existed=True)
    mock_user_repo.get_user_by_tg_id.assert_called_once_with(tg_id)
    mock_cache.set.assert_called_once_with(key=tg_id, value=user)


@pytest.mark.asyncio
async def test_get_or_create_creation(
    use_case: GetOrCreateUserIfNotExistUserCase,
    mock_cache: AsyncMock,
    mock_user_repo: AsyncMock,
) -> None:
    # Arrange
    tg_id = "123"
    user = User(id=1, tg_id=tg_id)
    mock_cache.get.return_value = None
    mock_user_repo.get_user_by_tg_id.return_value = None
    mock_user_repo.create_user.return_value = user

    # Act
    result = await use_case.execute(tg_id=tg_id)

    # Assert
    assert result == UserResult(user=user, is_existed=False)
    mock_user_repo.create_user.assert_called_once_with(
        tg_id=tg_id, username=None, role=None
    )
    mock_cache.set.assert_called_once_with(key=tg_id, value=user)


@pytest.mark.asyncio
async def test_get_or_create_validation_error(
    use_case: GetOrCreateUserIfNotExistUserCase,
) -> None:
    # Act & Assert
    with pytest.raises(ValueError, match="Either tg_id or username must be provided"):
        await use_case.execute(tg_id=None, username=None)
