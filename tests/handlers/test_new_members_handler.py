from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Chat, ChatMemberMember, ChatMemberUpdated, User
from punq import Container

from constants import Dialog
from dto.moderation import NewMemberRestrictionDTO
from handlers.group.new_members import process_chat_member_joined
from usecases.archive import NotifyArchiveChatNewMemberUseCase
from usecases.moderation import RestrictNewMemberUseCase


@pytest.mark.asyncio
async def test_process_chat_member_joined_human_with_antibot(
    mock_container: Container,
) -> None:
    """
    Тестирует вход нового участника (человека) в группу при включенном антиботе.

    Проверяет:
    1. Вызов RestrictNewMemberUseCase для ограничения прав пользователя.
    2. Формирование приветственного сообщения с ссылкой на верификацию.
    3. Использование кастомного текста приветствия.
    """
    # 1. Настройка моков
    restrict_usecase = AsyncMock(spec=RestrictNewMemberUseCase)
    notify_usecase = AsyncMock(spec=NotifyArchiveChatNewMemberUseCase)

    def resolve_side_effect(cls):
        if cls == RestrictNewMemberUseCase:
            return restrict_usecase
        if cls == NotifyArchiveChatNewMemberUseCase:
            return notify_usecase
        return MagicMock()

    mock_container.resolve.side_effect = resolve_side_effect

    verify_link = "https://t.me/my_bot?start=verify_123"
    custom_welcome = "Добро пожаловать, {username}!"
    restrict_usecase.execute.return_value = NewMemberRestrictionDTO(
        verify_link=verify_link,
        welcome_text=custom_welcome,
        is_antibot_enabled=True,
        show_welcome_text=True,
        auto_delete_welcome_text=False,
    )

    # 2. Мок ChatMemberUpdated
    user_id = 123
    username = "test_user"
    chat_id = -100123456789

    new_user = MagicMock(spec=User)
    new_user.id = user_id
    new_user.is_bot = False
    new_user.username = username
    new_user.first_name = "Test"

    new_chat_member = MagicMock(spec=ChatMemberMember)
    new_chat_member.user = new_user
    new_chat_member.status = "member"

    chat = MagicMock(spec=Chat)
    chat.id = chat_id
    chat.title = "Test Group"

    event = MagicMock(spec=ChatMemberUpdated)
    event.chat = chat
    event.new_chat_member = new_chat_member

    bot_mock = AsyncMock()
    bot_info = MagicMock(spec=User)
    bot_info.id = 999
    bot_info.username = "my_bot"
    bot_mock.get_me.return_value = bot_info
    bot_mock.send_message = AsyncMock()

    # 3. Вызов хендлера
    await process_chat_member_joined(
        event=event,
        container=mock_container,
        bot=bot_mock,
    )

    # 4. Проверки
    restrict_usecase.execute.assert_called_once_with(
        chat_tgid=str(chat_id), user_id=user_id, bot_username="my_bot"
    )

    expected_text = custom_welcome.format(
        username=username
    ) + Dialog.Antibot.VERIFIED_LINK.format(link=verify_link)
    bot_mock.send_message.assert_called_once()
    _, kwargs = bot_mock.send_message.call_args
    assert kwargs["chat_id"] == chat_id
    assert kwargs["text"] == expected_text
    assert kwargs["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_process_chat_member_joined_bot_joining(
    mock_container: Container,
) -> None:
    """
    Тестирует вход нового бота в группу.

    Проверяет:
    1. Что антибот не вызывается для участников-ботов.
    2. Что бот не отправляет приветствие при входе другого бота.
    """
    # 1. Настройка моков
    restrict_usecase = AsyncMock(spec=RestrictNewMemberUseCase)
    notify_usecase = AsyncMock(spec=NotifyArchiveChatNewMemberUseCase)

    def resolve_side_effect(cls):
        if cls == RestrictNewMemberUseCase:
            return restrict_usecase
        if cls == NotifyArchiveChatNewMemberUseCase:
            return notify_usecase
        return MagicMock()

    mock_container.resolve.side_effect = resolve_side_effect

    # 2. Мок ChatMemberUpdated с ботом
    chat = MagicMock(spec=Chat)
    chat.id = -100123
    chat.title = "Test Group"

    new_bot = MagicMock(spec=User)
    new_bot.id = 999
    new_bot.is_bot = True
    new_bot.username = "other_bot"

    new_chat_member = MagicMock(spec=ChatMemberMember)
    new_chat_member.user = new_bot
    new_chat_member.status = "member"

    event = MagicMock(spec=ChatMemberUpdated)
    event.chat = chat
    event.new_chat_member = new_chat_member

    bot_mock = AsyncMock()
    bot_info = MagicMock(spec=User)
    bot_info.id = 888
    bot_info.username = "my_bot"
    bot_mock.get_me.return_value = bot_info
    bot_mock.send_message = AsyncMock()

    # 3. Вызов хендлера
    await process_chat_member_joined(
        event=event,
        container=mock_container,
        bot=bot_mock,
    )

    # 4. Проверки
    restrict_usecase.execute.assert_not_called()
    notify_usecase.execute.assert_not_called()
    bot_mock.send_message.assert_not_called()
