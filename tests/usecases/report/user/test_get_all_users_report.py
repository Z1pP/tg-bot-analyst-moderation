"""Тесты GetAllUsersReportUseCase: пустой список пользователей, период, моки."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from constants.enums import UserRole
from dto.report import AllUsersReportDTO, AllUsersReportResultDTO
from models import User
from usecases.report.user.get_all_users_report import GetAllUsersReportUseCase


@pytest.fixture
def all_users_dto() -> AllUsersReportDTO:
    """DTO отчёта по всем пользователям."""
    start = datetime(2025, 1, 1, 9, 0, tzinfo=timezone.utc)
    end = datetime(2025, 1, 1, 18, 0, tzinfo=timezone.utc)
    return AllUsersReportDTO(
        user_tg_id="admin_1",
        start_date=start,
        end_date=end,
        selected_period="За сегодня",
    )


@pytest.fixture
def usecase() -> GetAllUsersReportUseCase:
    """Use case с замоканными зависимостями."""
    return GetAllUsersReportUseCase(
        msg_reply_repository=AsyncMock(),
        message_repository=AsyncMock(),
        user_repository=AsyncMock(),
        reaction_repository=AsyncMock(),
        chat_repository=AsyncMock(),
        punishment_repository=AsyncMock(),
        admin_action_log_service=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_execute_empty_tracked_users_returns_error_dto(
    usecase: GetAllUsersReportUseCase,
    all_users_dto: AllUsersReportDTO,
) -> None:
    """Пустой список отслеживаемых пользователей — error_message в DTO."""
    usecase._user_repository.get_tracked_users_for_admin = AsyncMock(return_value=[])

    result = await usecase.execute(all_users_dto)

    assert isinstance(result, AllUsersReportResultDTO)
    assert result.error_message is not None
    assert (
        "пользовател" in result.error_message.lower()
        or "пуст" in result.error_message.lower()
    )
    assert result.users_stats == []
    assert result.start_date is not None
    assert result.end_date is not None


@pytest.mark.asyncio
async def test_execute_with_users_no_activity_returns_empty_stats(
    usecase: GetAllUsersReportUseCase,
    all_users_dto: AllUsersReportDTO,
) -> None:
    """Пользователи есть, но нет сообщений/реакций/наказаний — в отчёт не попадают."""
    user = User(id=1, tg_id="u1", username="user1", role=UserRole.USER)
    usecase._user_repository.get_tracked_users_for_admin = AsyncMock(
        return_value=[user]
    )
    usecase._msg_reply_repository.get_replies_by_period_date_for_users = AsyncMock(
        return_value=[]
    )
    usecase._message_repository.get_messages_by_period_date_for_users = AsyncMock(
        return_value=[]
    )
    usecase._reaction_repository.get_reactions_by_user_and_period_for_users = AsyncMock(
        return_value=[]
    )
    usecase._punishment_repository.get_punishment_counts_by_moderators = AsyncMock(
        return_value={1: {"warns": 0, "bans": 0}}
    )

    result = await usecase.execute(all_users_dto)

    assert result.error_message is None
    assert result.users_stats == []
