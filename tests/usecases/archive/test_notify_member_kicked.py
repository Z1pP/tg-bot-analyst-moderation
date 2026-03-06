"""Тесты NotifyArchiveChatMemberKickedUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from dto import ArchiveMemberNotificationDTO
from usecases.archive.notify_member_kicked import NotifyArchiveChatMemberKickedUseCase


@pytest.fixture
def mock_chat_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_bot_message_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def usecase(
    mock_chat_service: AsyncMock,
    mock_bot_message_service: AsyncMock,
) -> NotifyArchiveChatMemberKickedUseCase:
    return NotifyArchiveChatMemberKickedUseCase(
        chat_service=mock_chat_service,
        bot_message_service=mock_bot_message_service,
    )


@pytest.fixture
def sample_dto() -> ArchiveMemberNotificationDTO:
    return ArchiveMemberNotificationDTO(
        chat_tgid="-100",
        user_tgid=12345,
        username="testuser",
        chat_title="Test Chat",
    )


@pytest.mark.asyncio
async def test_execute_skips_when_chat_not_found(
    usecase: NotifyArchiveChatMemberKickedUseCase,
    mock_chat_service: AsyncMock,
    mock_bot_message_service: AsyncMock,
    sample_dto: ArchiveMemberNotificationDTO,
) -> None:
    """При отсутствии чата уведомление не отправляется."""
    mock_chat_service.get_chat_with_archive = AsyncMock(return_value=None)

    await usecase.execute(sample_dto)

    mock_bot_message_service.send_chat_message.assert_not_called()


@pytest.mark.asyncio
async def test_execute_skips_when_no_archive_chat(
    usecase: NotifyArchiveChatMemberKickedUseCase,
    mock_chat_service: AsyncMock,
    mock_bot_message_service: AsyncMock,
    sample_dto: ArchiveMemberNotificationDTO,
) -> None:
    """При отсутствии привязанного архива уведомление не отправляется."""
    chat = MagicMock()
    chat.archive_chat_id = None
    mock_chat_service.get_chat_with_archive = AsyncMock(return_value=chat)

    await usecase.execute(sample_dto)

    mock_bot_message_service.send_chat_message.assert_not_called()


@pytest.mark.asyncio
async def test_execute_sends_notification_when_archive_exists(
    usecase: NotifyArchiveChatMemberKickedUseCase,
    mock_chat_service: AsyncMock,
    mock_bot_message_service: AsyncMock,
    sample_dto: ArchiveMemberNotificationDTO,
) -> None:
    """При наличии архива отправляется уведомление в архивный чат."""
    chat = MagicMock()
    chat.archive_chat_id = "-200"
    mock_chat_service.get_chat_with_archive = AsyncMock(return_value=chat)
    mock_bot_message_service.send_chat_message = AsyncMock()

    await usecase.execute(sample_dto)

    mock_bot_message_service.send_chat_message.assert_called_once()
    call_kwargs = mock_bot_message_service.send_chat_message.call_args
    assert call_kwargs.kwargs["chat_tgid"] == "-200"
    assert "testuser" in call_kwargs.kwargs["text"] or "@testuser" in call_kwargs.kwargs["text"]
    assert "12345" in call_kwargs.kwargs["text"]
    assert "Test Chat" in call_kwargs.kwargs["text"]


@pytest.mark.asyncio
async def test_execute_username_display_when_missing(
    usecase: NotifyArchiveChatMemberKickedUseCase,
    mock_chat_service: AsyncMock,
    mock_bot_message_service: AsyncMock,
) -> None:
    """При отсутствии username в текст подставляется 'Отсутствует'."""
    dto = ArchiveMemberNotificationDTO(
        chat_tgid="-100",
        user_tgid=12345,
        username="",
        chat_title="Test Chat",
    )
    chat = MagicMock()
    chat.archive_chat_id = "-200"
    mock_chat_service.get_chat_with_archive = AsyncMock(return_value=chat)
    mock_bot_message_service.send_chat_message = AsyncMock()

    await usecase.execute(dto)

    call_kwargs = mock_bot_message_service.send_chat_message.call_args
    assert "Отсутствует" in call_kwargs.kwargs["text"]
