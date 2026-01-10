import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants.callback import CallbackData

from ..common.navigation import show_chats_menu, show_main_menu

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Chat.BACK_TO_CHATS_MANAGEMENT)
async def show_chats_menu_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()
    await show_chats_menu(callback, state)


@router.callback_query(F.data == CallbackData.Chat.BACK_TO_MAIN_MENU_FROM_CHATS)
async def return_to_main_menu_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    user_language: str,
) -> None:
    """Обработчик возврата в главное меню из меню чатов"""
    await callback.answer()
    await show_main_menu(callback, state, user_language)
