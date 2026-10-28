"""Тесты детализации перерывов по чату: даты из периода вместо None."""

from datetime import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from constants.period import TimePeriod
from dto.report import ChatReportDTO
from models import ChatSession, User
from usecases.report.chat.get_chat_breaks_detail_report import (
    GetChatBreaksDetailReportUseCase,
)


@pytest.fixture
def usecase() -> GetChatBreaksDetailReportUseCase:
    return GetChatBreaksDetailReportUseCase(
        msg_reply_repository=AsyncMock(),
        message_repository=AsyncMock(),
        user_repository=AsyncMock(),
        reaction_repository=AsyncMock(),
        chat_repository=AsyncMock(),
        punishment_repository=AsyncMock(),
    )


def _chat() -> MagicMock:
    chat = MagicMock(spec=ChatSession)
    chat.start_time = time(9, 0)
    chat.end_time = time(18, 0)
    chat.tolerance = 10
    chat.breaks_time = 15
    return chat


@pytest.mark.asyncio
async def test_execute_resolves_dates_from_period(
    usecase: GetChatBreaksDetailReportUseCase,
) -> None:
    """Если start_date/end_date не заданы, они вычисляются из selected_period."""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "user"
    usecase._user_repository.get_tracked_users_for_admin.return_value = [user]
    usecase._chat_repository.get_chat_by_id.return_value = _chat()
    usecase._message_repository.get_messages_by_chat_id_and_period.return_value = []
    usecase._reaction_repository.get_reactions_by_chat_and_period.return_value = []
    dto = ChatReportDTO(
        chat_id=1,
        admin_tg_id="42",
        selected_period=TimePeriod.TODAY.value,
    )

    result = await usecase.execute(dto)

    assert result.error_message is None
    assert result.period
    call_kwargs = (
        usecase._message_repository.get_messages_by_chat_id_and_period.call_args.kwargs
    )
    assert call_kwargs["start_date"] is not None
    assert call_kwargs["end_date"] is not None