from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dto.buffer import BufferedMessageReplyDTO
from dto.message_reply import CreateMessageReplyDTO
from services import ChatService, UserService
from services.analytics_buffer_service import AnalyticsBufferService
from usecases.message.process_reply_message import SaveReplyMessageUseCase


@pytest.fixture
def mock_buffer_service() -> AsyncMock:
    return AsyncMock(spec=AnalyticsBufferService)


@pytest.fixture
def mock_user_service() -> AsyncMock:
    return AsyncMock(spec=UserService)


@pytest.fixture
def mock_chat_service() -> AsyncMock:
    return AsyncMock(spec=ChatService)


@pytest.fixture
def use_case(
    mock_buffer_service: AsyncMock,
    mock_user_service: AsyncMock,
    mock_chat_service: AsyncMock,
) -> SaveReplyMessageUseCase:
    return SaveReplyMessageUseCase(
        buffer_service=mock_buffer_service,
        user_service=mock_user_service,
        chat_service=mock_chat_service,
    )


@pytest.mark.asyncio
async def test_save_reply_message_success(
    use_case: SaveReplyMessageUseCase,
    mock_buffer_service: AsyncMock,
    mock_user_service: AsyncMock,
    mock_chat_service: AsyncMock,
) -> None:
    # Arrange
    now = datetime.now()

    mock_user = MagicMock()
    mock_user.id = 456
    mock_user_service.get_or_create.return_value = mock_user

    mock_chat = MagicMock()
    mock_chat.id = 123
    mock_chat_service.get_or_create.return_value = mock_chat

    reply_dto = CreateMessageReplyDTO(
        chat_tgid="123",
        original_message_url="http://t.me/c/123/1",
        reply_message_id=0,
        reply_user_tgid="456",
        original_message_date=now,
        reply_message_date=now,
        response_time_seconds=60,
        reply_message_id_str="msg_2",
    )

    with patch(
        "services.work_time_service.WorkTimeService.is_work_time", return_value=True
    ):
        # Act
        await use_case.execute(reply_dto)

    # Assert
    mock_user_service.get_or_create.assert_called_once_with(tg_id="456")
    mock_chat_service.get_or_create.assert_called_once_with(chat_tgid="123")
    mock_buffer_service.add_reply.assert_called_once()
    called_dto: BufferedMessageReplyDTO = mock_buffer_service.add_reply.call_args[0][0]

    assert isinstance(called_dto, BufferedMessageReplyDTO)
    assert called_dto.chat_id == 123
    assert called_dto.reply_message_id_str == reply_dto.reply_message_id_str


@pytest.mark.asyncio
async def test_save_reply_message_different_days(
    use_case: SaveReplyMessageUseCase,
    mock_buffer_service: AsyncMock,
    mock_user_service: AsyncMock,
    mock_chat_service: AsyncMock,
) -> None:
    # Arrange
    original_date = datetime(2023, 1, 1, 10, 0)
    reply_date = datetime(2023, 1, 2, 10, 0)

    mock_user = MagicMock()
    mock_user.id = 456
    mock_user_service.get_or_create.return_value = mock_user

    mock_chat = MagicMock()
    mock_chat.id = 123
    mock_chat_service.get_or_create.return_value = mock_chat

    reply_dto = CreateMessageReplyDTO(
        chat_tgid="123",
        original_message_url="http://t.me/c/123/1",
        reply_message_id=0,
        reply_user_tgid="456",
        original_message_date=original_date,
        reply_message_date=reply_date,
        response_time_seconds=60,
    )

    # Act
    await use_case.execute(reply_dto)

    # Assert
    mock_buffer_service.add_reply.assert_not_called()


@pytest.mark.asyncio
async def test_save_reply_message_outside_work_time(
    use_case: SaveReplyMessageUseCase,
    mock_buffer_service: AsyncMock,
    mock_user_service: AsyncMock,
    mock_chat_service: AsyncMock,
) -> None:
    # Arrange
    now = datetime.now()

    mock_user = MagicMock()
    mock_user.id = 456
    mock_user_service.get_or_create.return_value = mock_user

    mock_chat = MagicMock()
    mock_chat.id = 123
    mock_chat_service.get_or_create.return_value = mock_chat

    reply_dto = CreateMessageReplyDTO(
        chat_tgid="123",
        original_message_url="http://t.me/c/123/1",
        reply_message_id=0,
        reply_user_tgid="456",
        original_message_date=now,
        reply_message_date=now,
        response_time_seconds=60,
    )

    with patch(
        "services.work_time_service.WorkTimeService.is_work_time", return_value=False
    ):
        # Act
        await use_case.execute(reply_dto)

    # Assert
    mock_buffer_service.add_reply.assert_not_called()


@pytest.mark.asyncio
async def test_save_reply_message_fallback_id_str(
    use_case: SaveReplyMessageUseCase,
    mock_buffer_service: AsyncMock,
    mock_user_service: AsyncMock,
    mock_chat_service: AsyncMock,
) -> None:
    # Arrange
    now = datetime.now()

    mock_user = MagicMock()
    mock_user.id = 456
    mock_user_service.get_or_create.return_value = mock_user

    mock_chat = MagicMock()
    mock_chat.id = 123
    mock_chat_service.get_or_create.return_value = mock_chat

    reply_dto = CreateMessageReplyDTO(
        chat_tgid="123",
        original_message_url="http://t.me/c/123/1",
        reply_message_id=999,
        reply_user_tgid="456",
        original_message_date=now,
        reply_message_date=now,
        response_time_seconds=60,
        reply_message_id_str="",  # Force fallback
    )

    with patch(
        "services.work_time_service.WorkTimeService.is_work_time", return_value=True
    ):
        # Act
        await use_case.execute(reply_dto)

    # Assert
    mock_buffer_service.add_reply.assert_called_once()
    called_dto: BufferedMessageReplyDTO = mock_buffer_service.add_reply.call_args[0][0]
    assert called_dto.reply_message_id_str == "999"
