"""Модуль централизованной обработки ошибок модерации.

Предоставляет инструменты для унифицированного отображения ошибок пользователю
и управления состоянием FSM при возникновении исключительных ситуаций.
"""

import logging
from typing import Optional, Union

from aiogram import types
from aiogram.fsm.context import FSMContext

from keyboards.inline.moderation import moderation_menu_ikb
from utils.send_message import safe_edit_message

logger = logging.getLogger(__name__)


async def handle_moderation_error(
    event: Union[types.Message, types.CallbackQuery],
    state: FSMContext,
    text: str,
    message_to_edit_id: Optional[int] = None,
    reply_markup: Optional[types.InlineKeyboardMarkup] = moderation_menu_ikb(),
    clear_state: bool = False,
) -> None:
    """Централизованно обрабатывает и отображает ошибки модерации.

    Args:
        event: Объект события (сообщение или callback), вызвавшего ошибку.
        state: Контекст состояния FSM.
        text: Текст сообщения об ошибке для пользователя.
        message_to_edit_id: ID сообщения для редактирования (если event - Message).
        reply_markup: Клавиатура для сообщения об ошибке. По умолчанию - меню модерации.
        clear_state: Флаг необходимости полной очистки состояния FSM.
    """
    bot = event.bot
    chat_id = (
        event.chat.id if isinstance(event, types.Message) else event.message.chat.id
    )

    if isinstance(event, types.CallbackQuery):
        message_id = event.message.message_id
    else:
        message_id = message_to_edit_id

    await safe_edit_message(
        bot=bot,
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=reply_markup,
    )

    if clear_state:
        await state.clear()


async def handle_chats_error(
    callback: types.CallbackQuery,
    state: FSMContext,
    violator_username: str,
    error: Exception = None,
) -> None:
    """Обрабатывает ошибки, возникающие при получении списка чатов.

    Args:
        callback: Объект callback-запроса.
        state: Контекст состояния FSM.
        violator_username: Username пользователя, для которого искались чаты.
        error: Объект исключения (если есть) для логирования.
    """
    if error:
        logger.error("Ошибка получения чатов: %s", error, exc_info=True)
        text = "❌️ Произошла ошибка при получении списка чатов. Попробуйте еще раз."
    else:
        text = (
            f"❌️ Мы не нашли чатов, где @{violator_username} получил ограничение. "
            "Перепроверьте введённые данные, либо попробуйте снять ограничение вручную."
        )

    await handle_moderation_error(
        event=callback,
        state=state,
        text=text,
        clear_state=True,
    )
