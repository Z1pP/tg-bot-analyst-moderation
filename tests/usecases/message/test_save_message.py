from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from dto.buffer import BufferedMessageDTO
from dto.message import CreateMessageDTO
from services.analytics_buffer_service import AnalyticsBufferService
from usecases.message.save_message import SaveMessageUseCase


@pytest.mark.asyncio
async def test_save_message_success() -> None:
    # Arrange
    mock_buffer_service = AsyncMock(spec=AnalyticsBufferService)
    use_case = SaveMessageUseCase(buffer_service=mock_buffer_service)

    message_dto = CreateMessageDTO(
        chat_id=123,
        user_id=456,
        message_id="msg_1",
        message_type="text",
        content_type="text",
        text="Hello world",
        created_at=datetime.now(),
    )

    # Act
    await use_case.execute(message_dto)

    # Assert
    mock_buffer_service.add_message.assert_called_once()
    called_dto: BufferedMessageDTO = mock_buffer_service.add_message.call_args[0][0]

    assert isinstance(called_dto, BufferedMessageDTO)
    assert called_dto.chat_id == message_dto.chat_id
    assert called_dto.user_id == message_dto.user_id
    assert called_dto.message_id == message_dto.message_id
    assert called_dto.message_type == message_dto.message_type
    assert called_dto.content_type == message_dto.content_type
    assert called_dto.text == message_dto.text
    assert called_dto.created_at == message_dto.created_at
