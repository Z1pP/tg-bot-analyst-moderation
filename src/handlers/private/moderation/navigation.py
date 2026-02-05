"""Модуль навигации по меню модерации.

Содержит обработчики для отображения главного меню модерации
и управления переходами между разделами.
"""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.moderation import moderation_menu_ikb
from utils.send_message import safe_edit_message

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.Moderation.SHOW_MENU)
async def moderation_menu_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Отображает главное меню модерации.

    Args:
        callback: Объект callback-запроса от кнопки 'Меню модерации'.
        state: Контекст состояния FSM.

    State:
        Выполняет: state.clear() для сброса всех текущих процессов модерации.
    """
    await callback.answer()
    await state.clear()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Moderation.SELECT_ACTION,
        reply_markup=moderation_menu_ikb(),
    )
