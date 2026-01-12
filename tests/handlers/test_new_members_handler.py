from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Chat, Message, User

from constants import Dialog
from handlers.group.new_members import process_new_chat_members
from usecases.moderation import RestrictNewMemberUseCase


@pytest.mark.asyncio
async def test_process_new_chat_members_human_with_antibot(mock_container):
    # 1. Настройка моков
    restrict_usecase = AsyncMock(spec=RestrictNewMemberUseCase)
    mock_container.resolve.return_value = restrict_usecase

    verify_link = "https://t.me/my_bot?start=verify_123"
    custom_welcome = "Добро пожаловать, {username}!"
    restrict_usecase.execute.return_value = (verify_link, custom_welcome)

    # Мок сообщения
    user_id = 123
    username = "test_user"
    chat_id = -100123456789

    message = AsyncMock(spec=Message)
    message.chat = MagicMock(spec=Chat)
    message.chat.id = chat_id
    message.chat.title = "Test Group"

    new_user = MagicMock(spec=User)
    new_user.id = user_id
    new_user.is_bot = False
    new_user.username = username
    new_user.first_name = "Test"

    message.new_chat_members = [new_user]

    # Мок бота в сообщении
    bot_mock = AsyncMock()
    bot_info = MagicMock(spec=User)
    bot_info.username = "my_bot"
    bot_mock.get_me.return_value = bot_info
    message.bot = bot_mock

    message.answer = AsyncMock()

    # 2. Вызов хендлера
    await process_new_chat_members(message=message, container=mock_container)

    # 3. Проверки
    restrict_usecase.execute.assert_called_once_with(
        chat_tgid=str(chat_id), user_id=user_id, bot_username="my_bot"
    )

    expected_text = custom_welcome.format(
        username=username
    ) + Dialog.Antibot.VERIFIED_LINK.format(link=verify_link)
    message.answer.assert_called_once()
    _, kwargs = message.answer.call_args
    assert kwargs["text"] == expected_text
    assert kwargs["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_process_new_chat_members_bot_joining(mock_container):
    # 1. Настройка моков
    restrict_usecase = AsyncMock(spec=RestrictNewMemberUseCase)
    mock_container.resolve.return_value = restrict_usecase

    # Мок сообщения
    message = AsyncMock(spec=Message)
    message.chat = MagicMock(spec=Chat)
    message.chat.id = -100123
    message.chat.title = "Test Group"

    # Заходит бот
    new_bot = MagicMock(spec=User)
    new_bot.id = 999
    new_bot.is_bot = True
    new_bot.username = "other_bot"

    message.new_chat_members = [new_bot]
    message.answer = AsyncMock()

    # 2. Вызов хендлера
    await process_new_chat_members(message=message, container=mock_container)

    # 3. Проверки
    # Для ботов антибот не должен срабатывать
    restrict_usecase.execute.assert_not_called()
    message.answer.assert_not_called()
