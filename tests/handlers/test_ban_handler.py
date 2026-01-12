from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.enums import ChatType
from aiogram.types import Chat, Message, User

from dto import ModerationActionDTO
from handlers.group.moderation.ban import ban_user_handler
from usecases.moderation import GiveUserBanUseCase


@pytest.mark.asyncio
async def test_ban_user_handler_success(mock_container):
    # 1. Создаем мок UseCase
    mock_usecase = AsyncMock(spec=GiveUserBanUseCase)
    # Настраиваем контейнер возвращать наш мок при запросе GiveUserBanUseCase
    mock_container.resolve.return_value = mock_usecase

    # 2. Создаем данные для сообщения
    admin_id = 111
    violator_id = 222
    chat_id = -100333
    now = datetime.now()

    # Мокаем оригинальное сообщение (/ban)
    message = AsyncMock(spec=Message)
    message.message_id = 10
    message.text = "/ban Плохое поведение"
    message.date = now

    message.from_user = MagicMock(spec=User)
    message.from_user.id = admin_id
    message.from_user.username = "admin_user"

    message.chat = MagicMock(spec=Chat)
    message.chat.id = chat_id
    message.chat.title = "Test Chat"
    message.chat.type = ChatType.GROUP

    # Мокаем сообщение, на которое отвечаем (сообщение нарушителя)
    reply_message = MagicMock(spec=Message)
    reply_message.message_id = 5
    reply_message.date = now
    reply_message.from_user = MagicMock(spec=User)
    reply_message.from_user.id = violator_id
    reply_message.from_user.username = "violator_user"

    message.reply_to_message = reply_message

    # 3. Вызываем хендлер
    await ban_user_handler(message=message, container=mock_container)

    # 4. Проверяем, что UseCase был вызван
    mock_container.resolve.assert_called_once_with(GiveUserBanUseCase)
    mock_usecase.execute.assert_called_once()

    # Можно проверить, что в UseCase пришел правильный DTO
    call_args = mock_usecase.execute.call_args[1]
    dto = call_args["dto"]
    assert isinstance(dto, ModerationActionDTO)
    assert dto.violator_tgid == str(violator_id)
    assert dto.reason == "Плохое поведение"
    assert dto.admin_tgid == str(admin_id)
