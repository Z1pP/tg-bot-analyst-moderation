from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from dto.buffer import BufferedMessageDTO
from dto.message import CreateMessageDTO
from services.analytics_buffer_service import AnalyticsBufferService
from services.chat.chat_service import ChatService
from services.user.user_service import UserService
from usecases.message.save_message import SaveMessageUseCase


@pytest.mark.asyncio
async def test_save_message_success() -> None:
    # Arrange
    mock_buffer_service = AsyncMock(spec=AnalyticsBufferService)
    mock_user_service = AsyncMock(spec=UserService)
    mock_chat_service = AsyncMock(spec=ChatService)

    use_case = SaveMessageUseCase(
        buffer_service=mock_buffer_service,
        user_service=mock_user_service,
        chat_service=mock_chat_service,
    )

    # Мокаем возвращаемые значения от сервисов
    mock_user = MagicMock()
    mock_user.id = 456
    mock_user_service.get_or_create.return_value = mock_user

    mock_chat = MagicMock()
    mock_chat.id = 123
    mock_chat_service.get_or_create.return_value = mock_chat

    message_dto = CreateMessageDTO(
        chat_tgid="123",
        user_tgid="456",
        message_id="msg_1",
        message_type="message",
        content_type="text",
        text="Hello world",
        created_at=datetime.now(),
    )

    # Act
    await use_case.execute(message_dto)

    # Assert
    mock_user_service.get_or_create.assert_called_once_with(tg_id="456")
    mock_chat_service.get_or_create.assert_called_once_with(chat_tgid="123")
    mock_buffer_service.add_message.assert_called_once()
    called_dto: BufferedMessageDTO = mock_buffer_service.add_message.call_args[0][0]

    assert isinstance(called_dto, BufferedMessageDTO)
    assert called_dto.chat_id == 123
    assert called_dto.user_id == 456
    assert called_dto.message_id == message_dto.message_id
    assert called_dto.message_type == message_dto.message_type
    assert called_dto.content_type == message_dto.content_type
    assert called_dto.text == message_dto.text
    assert called_dto.created_at == message_dto.created_at
