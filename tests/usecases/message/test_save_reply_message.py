from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from dto.buffer import BufferedMessageReplyDTO
from dto.message_reply import CreateMessageReplyDTO
from services.analytics_buffer_service import AnalyticsBufferService
from usecases.message.process_reply_message import SaveReplyMessageUseCase


@pytest.fixture
def mock_buffer_service() -> AsyncMock:
    return AsyncMock(spec=AnalyticsBufferService)


@pytest.fixture
def use_case(mock_buffer_service: AsyncMock) -> SaveReplyMessageUseCase:
    return SaveReplyMessageUseCase(buffer_service=mock_buffer_service)


@pytest.mark.asyncio
async def test_save_reply_message_success(
    use_case: SaveReplyMessageUseCase, mock_buffer_service: AsyncMock
) -> None:
    # Arrange
    now = datetime.now()
    reply_dto = CreateMessageReplyDTO(
        chat_id=123,
        original_message_url="http://t.me/c/123/1",
        reply_message_id=2,
        reply_user_id=456,
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
    mock_buffer_service.add_reply.assert_called_once()
    called_dto: BufferedMessageReplyDTO = mock_buffer_service.add_reply.call_args[0][0]

    assert isinstance(called_dto, BufferedMessageReplyDTO)
    assert called_dto.chat_id == reply_dto.chat_id
    assert called_dto.reply_message_id_str == reply_dto.reply_message_id_str


@pytest.mark.asyncio
async def test_save_reply_message_different_days(
    use_case: SaveReplyMessageUseCase, mock_buffer_service: AsyncMock
) -> None:
    # Arrange
    original_date = datetime(2023, 1, 1, 10, 0)
    reply_date = datetime(2023, 1, 2, 10, 0)
    reply_dto = CreateMessageReplyDTO(
        chat_id=123,
        original_message_url="http://t.me/c/123/1",
        reply_message_id=2,
        reply_user_id=456,
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
    use_case: SaveReplyMessageUseCase, mock_buffer_service: AsyncMock
) -> None:
    # Arrange
    now = datetime.now()
    reply_dto = CreateMessageReplyDTO(
        chat_id=123,
        original_message_url="http://t.me/c/123/1",
        reply_message_id=2,
        reply_user_id=456,
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
    use_case: SaveReplyMessageUseCase, mock_buffer_service: AsyncMock
) -> None:
    # Arrange
    now = datetime.now()
    reply_dto = CreateMessageReplyDTO(
        chat_id=123,
        original_message_url="http://t.me/c/123/1",
        reply_message_id=999,
        reply_user_id=456,
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
