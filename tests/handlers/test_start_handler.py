from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.enums import ChatType
from aiogram.types import Chat, Message
from aiogram.types import User as TgUser

from constants import Dialog
from handlers.private.common.start_handler import start_handler
from keyboards.inline.menu import main_menu_ikb
from models import User
from usecases.user import GetUserByTgIdUseCase


@pytest.mark.asyncio
async def test_start_handler(mock_container: MagicMock) -> None:
    """
    Тестирует базовый хендлер команды /start.

    Проверяет:
    1. Формирование приветственного текста с именем пользователя.
    2. Генерацию инлайн-клавиатуры.
    3. Вызов метода answer у сообщения.
    """
    user_id = 12345678
    full_name = "Test User"
    user_language = "ru"

    db_user = User(id=1, tg_id=str(user_id), username=full_name)
    mock_usecase = AsyncMock(spec=GetUserByTgIdUseCase)
    mock_usecase.execute.return_value = db_user
    mock_container.resolve.return_value = mock_usecase

    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    message.from_user = MagicMock(spec=TgUser)
    message.from_user.id = user_id
    message.from_user.full_name = full_name

    message.chat = MagicMock(spec=Chat)
    message.chat.id = user_id
    message.chat.type = ChatType.PRIVATE

    await start_handler(
        message=message, container=mock_container, user_language=user_language
    )

    expected_text = Dialog.Menu.MENU_TEXT.format(username=full_name)
    expected_markup = main_menu_ikb(user=db_user, user_language=user_language)

    message.answer.assert_called_once()
    _, kwargs = message.answer.call_args
    assert kwargs["text"] == expected_text
    assert kwargs["reply_markup"].model_dump(
        exclude_none=True
    ) == expected_markup.model_dump(exclude_none=True)
