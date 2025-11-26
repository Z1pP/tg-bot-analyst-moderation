import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from constants.callback import CallbackData
from constants.i18n import DEFAULT_LANGUAGE
from container import container
from keyboards.inline.chats import chats_management_ikb
from keyboards.inline.menu import admin_menu_ikb
from services.user import UserService
from states import MenuStates
from states.chat_states import ChatStateManager
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Chat.BACK_TO_CHATS_MANAGEMENT)
async def show_chats_menu_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()
    await state.clear()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.CHAT_MANAGEMENT,
        reply_markup=chats_management_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=ChatStateManager.chats_menu,
    )


@router.callback_query(F.data == CallbackData.Chat.BACK_TO_MAIN_MENU_FROM_CHATS)
async def return_to_main_menu_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик возврата в главное меню из меню чатов"""
    await callback.answer()
    await state.clear()

    username = callback.from_user.first_name
    menu_text = Dialog.Menu.MENU_TEXT.format(username=username)

    # Получаем язык пользователя из БД
    user_service: UserService = container.resolve(UserService)
    db_user = await user_service.get_user(tg_id=str(callback.from_user.id))
    user_language = (
        db_user.language if db_user and db_user.language else DEFAULT_LANGUAGE
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=menu_text,
        reply_markup=admin_menu_ikb(user_language, admin_tg_id=callback.from_user.id),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=MenuStates.main_menu,
    )
