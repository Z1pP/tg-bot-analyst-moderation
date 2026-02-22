"""Тесты для GetSingleUserReportUseCase: ветка no_chats, UserNotFoundException."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from constants.enums import UserRole
from dto import SingleUserReportDTO
from exceptions.user import UserNotFoundException
from models import User
from usecases.report.user.get_single_user_report import GetSingleUserReportUseCase


@pytest.fixture
def report_dto() -> SingleUserReportDTO:
    start = datetime(2025, 1, 1, 9, 0, tzinfo=timezone.utc)
    end = datetime(2025, 1, 1, 18, 0, tzinfo=timezone.utc)
    return SingleUserReportDTO(
        user_id=1,
        admin_tg_id="20",
        start_date=start,
        end_date=end,
        selected_period="day",
    )


@pytest.fixture
def sample_user() -> User:
    return User(id=1, tg_id="10", username="user", role=UserRole.USER)


@pytest.fixture
def usecase() -> GetSingleUserReportUseCase:
    return GetSingleUserReportUseCase(
        msg_reply_repository=AsyncMock(),
        message_repository=AsyncMock(),
        user_repository=AsyncMock(),
        reaction_repository=AsyncMock(),
        chat_repository=AsyncMock(),
        punishment_repository=AsyncMock(),
        admin_action_log_service=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_execute_no_tracked_chats_returns_error_message(
    usecase: GetSingleUserReportUseCase,
    report_dto: SingleUserReportDTO,
    sample_user: User,
) -> None:
    """Если у админа нет отслеживаемых чатов — возвращается error_message и no_chats."""
    usecase._user_repository.get_user_by_id = AsyncMock(return_value=sample_user)
    usecase._chat_repository.get_tracked_chats_for_admin = AsyncMock(return_value=[])

    result = await usecase.execute(report_dto=report_dto)

    assert result.error_message == "⚠️ Необходимо добавить чат в отслеживание."
    assert result.username == sample_user.username
    assert result.user_id == sample_user.id
    assert result.day_stats is None
    assert result.multi_day_stats is None
    assert result.replies_stats.total_count == 0


@pytest.mark.asyncio
async def test_execute_user_not_found_raises(
    usecase: GetSingleUserReportUseCase,
    report_dto: SingleUserReportDTO,
) -> None:
    """Если пользователь не найден — выбрасывается UserNotFoundException."""
    usecase._user_repository.get_user_by_id = AsyncMock(return_value=None)

    with pytest.raises(UserNotFoundException):
        await usecase.execute(report_dto=report_dto)
