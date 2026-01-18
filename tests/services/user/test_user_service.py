from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from constants.enums import UserRole
from models import User
from repositories.user_repository import UserRepository
from services.caching.base import ICache
from services.user.user_service import UserService


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def mock_cache() -> AsyncMock:
    return AsyncMock(spec=ICache)


@pytest.fixture
def user_service(mock_repo: AsyncMock, mock_cache: AsyncMock) -> UserService:
    return UserService(user_repository=mock_repo, cache=mock_cache)


@pytest.fixture
def sample_user() -> User:
    return User(id=1, tg_id="12345", username="test_user", role=UserRole.USER)


@pytest.mark.asyncio
async def test_get_user_by_id_cache_hit(
    user_service: UserService,
    mock_cache: AsyncMock,
    mock_repo: AsyncMock,
    sample_user: User,
) -> None:
    # Arrange
    user_id = 1
    mock_cache.get.return_value = sample_user

    # Act
    result = await user_service.get_user_by_id(user_id)

    # Assert
    assert result == sample_user
    mock_cache.get.assert_called_once_with(f"user:id:{user_id}")
    mock_repo.get_user_by_id.assert_not_called()


@pytest.mark.asyncio
async def test_get_user_by_id_cache_miss_db_hit(
    user_service: UserService,
    mock_cache: AsyncMock,
    mock_repo: AsyncMock,
    sample_user: User,
) -> None:
    # Arrange
    user_id = 1
    mock_cache.get.return_value = None
    mock_repo.get_user_by_id.return_value = sample_user

    # Act
    result = await user_service.get_user_by_id(user_id)

    # Assert
    assert result == sample_user
    mock_cache.get.assert_called_once_with(f"user:id:{user_id}")
    mock_repo.get_user_by_id.assert_called_once_with(user_id=user_id)
    # Verify caching (by id, tg_id, username)
    assert mock_cache.set.call_count == 3


@pytest.mark.asyncio
async def test_get_user_by_id_cache_miss_db_miss(
    user_service: UserService, mock_cache: AsyncMock, mock_repo: AsyncMock
) -> None:
    # Arrange
    user_id = 999
    mock_cache.get.return_value = None
    mock_repo.get_user_by_id.return_value = None

    # Act
    result = await user_service.get_user_by_id(user_id)

    # Assert
    assert result is None
    mock_cache.set.assert_not_called()


@pytest.mark.asyncio
async def test_get_user_cache_hit_tg_id(
    user_service: UserService, mock_cache: AsyncMock, sample_user: User
) -> None:
    # Arrange
    tg_id = "12345"
    mock_cache.get.return_value = sample_user

    # Act
    result = await user_service.get_user(tg_id=tg_id)

    # Assert
    assert result == sample_user
    mock_cache.get.assert_called_once_with(f"user:tg_id:{tg_id}")


@pytest.mark.asyncio
async def test_get_user_cache_hit_tg_id_username_change(
    user_service: UserService,
    mock_cache: AsyncMock,
    mock_repo: AsyncMock,
    sample_user: User,
) -> None:
    # Arrange
    tg_id = "12345"
    old_username = "old_user"
    new_username = "new_user"
    sample_user.username = old_username
    mock_cache.get.return_value = sample_user

    updated_user = User(id=1, tg_id=tg_id, username=new_username)
    mock_repo.update_user.return_value = updated_user

    # Act
    result = await user_service.get_user(tg_id=tg_id, username=new_username)

    # Assert
    assert result.username == new_username
    mock_repo.update_user.assert_called_once_with(
        user_id=sample_user.id, username=new_username
    )
    # Check re-caching
    assert mock_cache.set.call_count == 3


@pytest.mark.asyncio
async def test_get_user_cache_hit_username(
    user_service: UserService, mock_cache: AsyncMock, sample_user: User
) -> None:
    # Arrange
    username = "test_user"
    # First call for tg_id returns None, second for username returns user
    mock_cache.get.side_effect = [None, sample_user]

    # Act
    result = await user_service.get_user(tg_id="some_id", username=username)

    # Assert
    assert result == sample_user
    assert mock_cache.get.call_count == 2


@pytest.mark.asyncio
async def test_create_user(
    user_service: UserService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_user: User,
) -> None:
    # Arrange
    tg_id = "12345"
    username = "test_user"
    mock_repo.create_user.return_value = sample_user

    # Act
    result = await user_service.create_user(tg_id=tg_id, username=username)

    # Assert
    assert result == sample_user
    mock_repo.create_user.assert_called_once_with(
        tg_id=tg_id, username=username, role=UserRole.USER, language="ru"
    )
    assert mock_cache.set.call_count == 3


@pytest.mark.asyncio
async def test_get_or_create_existing(
    user_service: UserService, sample_user: User
) -> None:
    # Arrange
    # Mock internal get_user
    user_service.get_user = AsyncMock(return_value=sample_user)

    # Act
    result = await user_service.get_or_create(tg_id="12345", username="test_user")

    # Assert
    assert result == sample_user
    user_service.get_user.assert_called_once()


@pytest.mark.asyncio
async def test_get_or_create_new(
    user_service: UserService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_user: User,
) -> None:
    # Arrange
    user_service.get_user = AsyncMock(return_value=None)
    user_service.create_user = AsyncMock(return_value=sample_user)

    # Act
    result = await user_service.get_or_create(tg_id="12345", username="test_user")

    # Assert
    assert result == sample_user
    user_service.create_user.assert_called_once()


@pytest.mark.asyncio
async def test_get_or_create_race_condition(
    user_service: UserService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_user: User,
) -> None:
    # Arrange
    user_service.get_user = AsyncMock(side_effect=[None, sample_user])
    # create_user raises IntegrityError due to parallel creation
    # We need to mock the real create_user method of the service or the repo it calls
    with patch.object(
        UserService,
        "create_user",
        side_effect=IntegrityError(
            "statement",
            "params",
            'duplicate key value violates unique constraint "users_tg_id_key"',
        ),
    ):
        # Act
        result = await user_service.get_or_create(tg_id="12345", username="test_user")

        # Assert
        assert result == sample_user
        assert user_service.get_user.call_count == 2
