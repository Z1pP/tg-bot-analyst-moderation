from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import (
    CallbackQuery,
    Chat,
    ChatMemberMember,
    ChatMemberUpdated,
    Message,
    User,
)
from punq import Container

from constants import Dialog
from dto import ArchiveMemberNotificationDTO, ResultVerifyMember
from dto.moderation import NewMemberRestrictionDTO
from handlers.group.new_members import (
    process_chat_member_joined,
    process_humanity_verification,
)
from usecases.archive import NotifyArchiveChatNewMemberUseCase
from usecases.moderation import RestrictNewMemberUseCase, VerifyMemberUseCase


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

    custom_welcome = "Добро пожаловать, {username}!"
    restrict_usecase.execute.return_value = NewMemberRestrictionDTO(
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
    bot_mock.send_message = AsyncMock()

    # 3. Вызов хендлера
    mock_kick_task = MagicMock()
    mock_kick_chain = MagicMock()
    mock_kick_chain.kiq = AsyncMock()
    mock_kick_chain.with_labels.return_value = mock_kick_chain
    mock_kick_task.kicker.return_value = mock_kick_chain
    with patch(
        "handlers.group.new_members.kick_unverified_member_task",
        mock_kick_task,
    ):
        await process_chat_member_joined(
            event=event,
            container=mock_container,
            bot=bot_mock,
        )

    # 4. Проверки
    restrict_usecase.execute.assert_called_once_with(
        chat_tgid=str(chat_id), user_id=user_id
    )
    notify_usecase.execute.assert_called_once_with(
        ArchiveMemberNotificationDTO(
            chat_tgid=str(chat_id),
            user_tgid=user_id,
            username=username,
            chat_title="Test Group",
        )
    )

    expected_text = (
        custom_welcome.format(username=username) + Dialog.Antibot.VERIFY_BUTTON_PROMPT
    )
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


@pytest.mark.asyncio
async def test_process_humanity_verification_deletes_message_and_answers_with_result(
    mock_container: Container,
) -> None:
    """
    При нажатии кнопки верификации: сообщение удаляется, ответ — result.message с show_alert.
    """
    from constants.callback import CallbackData

    verify_usecase = AsyncMock(spec=VerifyMemberUseCase)
    result_msg = "✅ Проверка пройдена! Теперь вы можете отправлять сообщения."
    verify_usecase.execute.return_value = ResultVerifyMember(
        unmuted=True,
        message=result_msg,
    )
    mock_container.resolve.side_effect = lambda cls: (
        verify_usecase if cls == VerifyMemberUseCase else MagicMock()
    )

    user_id = 456
    chat_id = -100999
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = user_id
    callback.data = f"{CallbackData.Antibot.CONFIRM_HUMANITY_PREFIX}{user_id}"
    callback.message = MagicMock(spec=Message)
    callback.message.chat = MagicMock()
    callback.message.chat.id = chat_id
    callback.message.chat.type = "supergroup"
    callback.message.delete = AsyncMock()
    callback.answer = AsyncMock()

    await process_humanity_verification(callback=callback, container=mock_container)

    verify_usecase.execute.assert_called_once_with(
        user_tgid=str(user_id),
        chat_tgid=str(chat_id),
    )
    callback.message.delete.assert_called_once()
    callback.answer.assert_called_once_with(result_msg, show_alert=True)


@pytest.mark.asyncio
async def test_process_humanity_verification_wrong_user_shows_error(
    mock_container: Container,
) -> None:
    """Если на кнопку нажал не тот пользователь — показывается VERIFIED_ERROR_USER, use case не вызывается."""
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 111
    callback.data = "confirm_humanity__222"  # кнопка для другого пользователя
    callback.answer = AsyncMock()

    await process_humanity_verification(callback=callback, container=mock_container)

    mock_container.resolve.assert_not_called()
    callback.answer.assert_called_once_with(
        Dialog.Antibot.VERIFIED_ERROR_USER,
        show_alert=True,
    )
