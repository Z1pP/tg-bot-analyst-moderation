from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.enums import ChatType
from aiogram.types import Chat, Message, User

from constants import Dialog
from handlers.private.common.start_handler import start_handler
from keyboards.inline.menu import admin_menu_ikb


@pytest.mark.asyncio
async def test_start_handler(mock_container):
    # 1. Настраиваем данные пользователя
    user_id = 12345678
    full_name = "Test User"
    user_language = "ru"

    # 2. Создаем мок сообщения
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()  # Явно указываем, что это асинхронный метод
    message.from_user = MagicMock(spec=User)
    message.from_user.id = user_id
    message.from_user.full_name = full_name

    message.chat = MagicMock(spec=Chat)
    message.chat.id = user_id
    message.chat.type = ChatType.PRIVATE

    # 3. Вызываем хендлер напрямую
    await start_handler(
        message=message, container=mock_container, user_language=user_language
    )

    # 4. Проверяем результат
    expected_text = Dialog.Menu.MENU_TEXT.format(username=full_name)
    expected_markup = admin_menu_ikb(
        user_language=user_language, admin_tg_id=str(user_id)
    )

    # Проверяем, что message.answer был вызван с правильными параметрами
    message.answer.assert_called_once()
    _, kwargs = message.answer.call_args

    assert kwargs["text"] == expected_text
    # Сравниваем клавиатуры (убеждаемся, что они совпадают по наполнению)
    assert kwargs["reply_markup"].model_dump(
        exclude_none=True
    ) == expected_markup.model_dump(exclude_none=True)
