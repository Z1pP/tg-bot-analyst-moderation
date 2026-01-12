from unittest.mock import AsyncMock

import pytest

from constants.enums import UserRole
from dto.user import UserDTO
from models import User
from repositories.user_repository import UserRepository
from usecases.user.create_new_user import CreateNewUserUserCase
from usecases.user.get_all_users import GetAllUsersUseCase
from usecases.user.get_user import GetUserByIdUseCase, GetUserByTgIdUseCase
from usecases.user.remove_user import DeleteUserUseCase


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    return AsyncMock(spec=UserRepository)


@pytest.mark.asyncio
async def test_create_new_user_usecase(mock_user_repo: AsyncMock) -> None:
    # Arrange
    use_case = CreateNewUserUserCase(user_repository=mock_user_repo)
    tg_id = "123"
    username = "test_user"
    mock_user_repo.create_user.return_value = User(id=1, tg_id=tg_id, username=username)

    # Act
    result = await use_case.execute(tg_id=tg_id, username=username)

    # Assert
    assert result.tg_id == tg_id
    mock_user_repo.create_user.assert_called_once_with(tg_id=tg_id, username=username)


@pytest.mark.asyncio
async def test_get_user_by_tg_id_usecase(mock_user_repo: AsyncMock) -> None:
    # Arrange
    use_case: GetUserByTgIdUseCase = GetUserByTgIdUseCase(
        user_repository=mock_user_repo
    )
    tg_id = "123"
    mock_user_repo.get_user_by_tg_id.return_value = User(id=1, tg_id=tg_id)

    # Act
    result = await use_case.execute(tg_id=tg_id)

    # Assert
    assert result.tg_id == tg_id
    mock_user_repo.get_user_by_tg_id.assert_called_once_with(tg_id=tg_id)


@pytest.mark.asyncio
async def test_get_user_by_id_usecase(mock_user_repo: AsyncMock) -> None:
    # Arrange
    use_case = GetUserByIdUseCase(user_repository=mock_user_repo)
    user_id = 1
    mock_user_repo.get_user_by_id.return_value = User(id=user_id)

    # Act
    result = await use_case.execute(user_id=user_id)

    # Assert
    assert result.id == user_id
    mock_user_repo.get_user_by_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_delete_user_usecase(mock_user_repo: AsyncMock) -> None:
    # Arrange
    use_case = DeleteUserUseCase(user_repository=mock_user_repo)
    user_id = 1
    mock_user_repo.delete_user.return_value = True

    # Act
    result = await use_case.execute(user_id=user_id)

    # Assert
    assert result is True
    mock_user_repo.delete_user.assert_called_once_with(user_id=user_id)


@pytest.mark.asyncio
async def test_get_all_users_usecase(mock_user_repo: AsyncMock) -> None:
    # Arrange
    use_case = GetAllUsersUseCase(user_repository=mock_user_repo)
    mock_user_repo.get_all_moderators.return_value = [
        User(id=1, username="mod1", role=UserRole.MODERATOR, is_active=True),
        User(id=2, username="mod2", role=UserRole.MODERATOR, is_active=True),
    ]

    # Act
    result = await use_case.execute()

    # Assert
    assert len(result) == 2
    assert isinstance(result[0], UserDTO)
    assert result[0].username == "mod1"
    mock_user_repo.get_all_moderators.assert_called_once()
