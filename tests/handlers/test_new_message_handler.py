from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.enums import ContentType
from aiogram.types import Chat, Message
from aiogram.types import User as TGUser

from handlers.group.new_message import group_message_handler
from models import ChatSession
from models import User as DBUser
from models.message import MessageType
from services.chat import ChatService
from services.user import UserService
from usecases.message import SaveMessageUseCase, SaveReplyMessageUseCase


@pytest.fixture
def mock_services(mock_container):
    # Мокаем сервисы
    user_service = AsyncMock(spec=UserService)
    chat_service = AsyncMock(spec=ChatService)
    save_msg_usecase = AsyncMock(spec=SaveMessageUseCase)
    save_reply_usecase = AsyncMock(spec=SaveReplyMessageUseCase)

    # Настраиваем контейнер
    def side_effect(cls):
        if cls == UserService:
            return user_service
        if cls == ChatService:
            return chat_service
        if cls == SaveMessageUseCase:
            return save_msg_usecase
        if cls == SaveReplyMessageUseCase:
            return save_reply_usecase
        return MagicMock()

    mock_container.resolve.side_effect = side_effect

    return {
        "user": user_service,
        "chat": chat_service,
        "save_msg": save_msg_usecase,
        "save_reply": save_reply_usecase,
    }


@pytest.mark.asyncio
async def test_group_message_handler_regular(mock_container, mock_services):
    # 1. Данные для моков
    db_user = MagicMock(spec=DBUser)
    db_user.id = 1
    mock_services["user"].get_or_create.return_value = db_user

    db_chat = MagicMock(spec=ChatSession)
    db_chat.id = 10
    db_chat.chat_id = "-100123"
    mock_services["chat"].get_or_create.return_value = db_chat

    # 2. Мок сообщения
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock(spec=TGUser)
    message.from_user.is_bot = False
    message.from_user.id = 123
    message.from_user.username = "testuser"

    message.chat = MagicMock(spec=Chat)
    message.chat.id = -100123
    message.chat.title = "Test Group"

    message.message_id = 555
    message.text = "Hello world"
    message.content_type = ContentType.TEXT
    message.date = datetime.now()
    message.reply_to_message = None

    # 3. Вызов
    await group_message_handler(message=message, container=mock_container)

    # 4. Проверки
    mock_services["user"].get_or_create.assert_called_once()
    mock_services["save_msg"].execute.assert_called_once()
    dto = mock_services["save_msg"].execute.call_args.kwargs["message_dto"]
    assert dto.message_type == MessageType.MESSAGE.value
    assert dto.text == "Hello world"
    mock_services["save_reply"].execute.assert_not_called()


@pytest.mark.asyncio
async def test_group_message_handler_reply(mock_container, mock_services):
    # 1. Данные для моков
    db_user = MagicMock(spec=DBUser)
    db_user.id = 1
    mock_services["user"].get_or_create.return_value = db_user

    db_chat = MagicMock(spec=ChatSession)
    db_chat.id = 10
    db_chat.chat_id = "-100123"
    mock_services["chat"].get_or_create.return_value = db_chat

    # 2. Мок сообщения (ответ на другое сообщение)
    original_date = datetime.now() - timedelta(seconds=30)
    reply_date = datetime.now()

    original_message = MagicMock(spec=Message)
    original_message.message_id = 100
    original_message.date = original_date

    message = AsyncMock(spec=Message)
    message.from_user = MagicMock(spec=TGUser)
    message.from_user.is_bot = False
    message.from_user.id = 123
    message.from_user.username = "testuser"

    message.chat = MagicMock(spec=Chat)
    message.chat.id = -100123
    message.chat.title = "Test Group"

    message.message_id = 101
    message.text = "This is a reply"
    message.content_type = ContentType.TEXT
    message.date = reply_date
    message.reply_to_message = original_message

    # 3. Вызов
    await group_message_handler(message=message, container=mock_container)

    # 4. Проверки
    # Проверяем сохранение самого сообщения
    assert mock_services["save_msg"].execute.call_count == 1
    msg_dto = mock_services["save_msg"].execute.call_args.kwargs["message_dto"]
    assert msg_dto.message_type == MessageType.REPLY.value

    # Проверяем сохранение связи Reply
    mock_services["save_reply"].execute.assert_called_once()
    reply_dto = mock_services["save_reply"].execute.call_args.kwargs[
        "reply_message_dto"
    ]

    # Проверяем расчет времени (30 секунд разницы)
    assert 29 <= reply_dto.response_time_seconds <= 31
    assert reply_dto.reply_message_id_str == "101"


@pytest.mark.asyncio
async def test_group_message_handler_ignore_bot(mock_container, mock_services):
    # 1. Мок сообщения от бота
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock(spec=TGUser)
    message.from_user.is_bot = True

    # 2. Вызов
    await group_message_handler(message=message, container=mock_container)

    # 3. Проверки - ничего не должно быть вызвано
    mock_services["user"].get_or_create.assert_not_called()
    mock_services["save_msg"].execute.assert_not_called()
