"""Тесты для AdminActionLogService."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from constants.enums import AdminActionType
from repositories import AdminActionLogRepository, UserRepository
from services.admin_action_log_service import AdminActionLogService


@pytest.fixture
def mock_log_repo() -> AsyncMock:
    return AsyncMock(spec=AdminActionLogRepository)


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def service(
    mock_log_repo: AsyncMock,
    mock_user_repo: AsyncMock,
) -> AdminActionLogService:
    return AdminActionLogService(
        log_repository=mock_log_repo,
        user_repository=mock_user_repo,
    )


@pytest.mark.asyncio
async def test_log_action_user_found(
    service: AdminActionLogService,
    mock_user_repo: AsyncMock,
    mock_log_repo: AsyncMock,
) -> None:
    """При найденном пользователе создаётся запись в логе."""
    admin = SimpleNamespace(id=1, tg_id="123", username="admin")
    mock_user_repo.get_user_by_tg_id = AsyncMock(return_value=admin)
    mock_log_repo.create_log = AsyncMock()

    await service.log_action(
        admin_tg_id="123",
        action_type=AdminActionType.REPORT_USER,
        details="Отчёт за период",
    )

    mock_user_repo.get_user_by_tg_id.assert_called_once_with(tg_id="123")
    mock_log_repo.create_log.assert_called_once_with(
        admin_id=admin.id,
        action_type=AdminActionType.REPORT_USER,
        details="Отчёт за период",
    )


@pytest.mark.asyncio
async def test_log_action_user_not_found(
    service: AdminActionLogService,
    mock_user_repo: AsyncMock,
    mock_log_repo: AsyncMock,
) -> None:
    """При ненайденном пользователе логирование не выполняется."""
    mock_user_repo.get_user_by_tg_id = AsyncMock(return_value=None)

    await service.log_action(
        admin_tg_id="unknown",
        action_type=AdminActionType.REPORT_USER,
    )

    mock_user_repo.get_user_by_tg_id.assert_called_once_with(tg_id="unknown")
    mock_log_repo.create_log.assert_not_called()


@pytest.mark.asyncio
async def test_log_action_details_none(
    service: AdminActionLogService,
    mock_user_repo: AsyncMock,
    mock_log_repo: AsyncMock,
) -> None:
    """create_log вызывается с details=None если не переданы."""
    admin = SimpleNamespace(id=10, tg_id="1", username="a")
    mock_user_repo.get_user_by_tg_id = AsyncMock(return_value=admin)
    mock_log_repo.create_log = AsyncMock()

    await service.log_action(admin_tg_id="1", action_type=AdminActionType.REPORT_USER)

    mock_log_repo.create_log.assert_called_once_with(
        admin_id=admin.id,
        action_type=AdminActionType.REPORT_USER,
        details=None,
    )


@pytest.mark.asyncio
async def test_log_action_db_error_swallowed(
    service: AdminActionLogService,
    mock_user_repo: AsyncMock,
    mock_log_repo: AsyncMock,
) -> None:
    """При SQLAlchemyError логирование не пробрасывает исключение."""
    admin = SimpleNamespace(id=10, tg_id="1", username="a")
    mock_user_repo.get_user_by_tg_id = AsyncMock(return_value=admin)
    mock_log_repo.create_log = AsyncMock(side_effect=SQLAlchemyError("db error"))

    await service.log_action(admin_tg_id="1", action_type=AdminActionType.REPORT_USER)
    mock_log_repo.create_log.assert_called_once()
