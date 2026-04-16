"""Тесты RecordChatMembershipEventUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from constants.enums import MembershipEventType
from dto.membership_event import RecordChatMembershipEventDTO
from usecases.membership.record_chat_membership_event import (
    RecordChatMembershipEventUseCase,
)


@pytest.fixture
def usecase() -> RecordChatMembershipEventUseCase:
    chat_service = MagicMock()
    membership_repository = MagicMock()
    membership_repository.add = AsyncMock()
    return RecordChatMembershipEventUseCase(
        chat_service=chat_service,
        membership_event_repository=membership_repository,
    )


@pytest.mark.asyncio
async def test_execute_chat_not_found_skips_add(
    usecase: RecordChatMembershipEventUseCase,
) -> None:
    """Если чата нет в БД, в репозиторий событий не пишем."""
    usecase._chat_service.get_chat = AsyncMock(return_value=None)
    dto = RecordChatMembershipEventDTO(
        chat_tgid="-100",
        user_tgid=42,
        event_type=MembershipEventType.JOIN,
    )
    await usecase.execute(dto)
    usecase._membership_event_repository.add.assert_not_called()


@pytest.mark.asyncio
async def test_execute_chat_found_calls_add(
    usecase: RecordChatMembershipEventUseCase,
) -> None:
    """При наличии чата вызывается add с внутренним id сессии."""
    chat = MagicMock()
    chat.id = 7
    usecase._chat_service.get_chat = AsyncMock(return_value=chat)
    dto = RecordChatMembershipEventDTO(
        chat_tgid="-100",
        user_tgid=99,
        event_type=MembershipEventType.LEFT,
    )
    await usecase.execute(dto)
    usecase._membership_event_repository.add.assert_awaited_once_with(
        chat_id=7,
        user_tgid=99,
        event_type=MembershipEventType.LEFT,
    )
