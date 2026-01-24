import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from keyboards.inline.menu import main_menu_ikb
from keyboards.inline.message_actions import send_message_ikb
from states import MenuStates, MessageManagerState
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "message_management_menu")
async def message_management_menu_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик возврата в меню управления сообщениями."""
    await callback.answer()

    logger.info(
        "Администратор %s вернулся в меню управления сообщениями",
        callback.from_user.username,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Messages.INPUT_MESSAGE_LINK,
        reply_markup=send_message_ikb(),
    )

    # Сохраняем message_id для последующего редактирования
    await state.update_data(active_message_id=callback.message.message_id)

    await state.set_state(MessageManagerState.waiting_message_link)


@router.callback_query(F.data == "back_to_main_menu_from_message_management")
async def back_to_main_menu_from_message_management_handler(
    callback: types.CallbackQuery, state: FSMContext, user_language: str
) -> None:
    """Обработчик возврата в главное меню из меню управления сообщениями"""
    await callback.answer()
    await state.clear()

    username = callback.from_user.first_name
    menu_text = Dialog.Menu.MENU_TEXT.format(username=username)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=menu_text,
        reply_markup=main_menu_ikb(
            user=None,
            user_language=user_language,
            admin_tg_id=str(callback.from_user.id),
        ),
    )

    await state.set_state(MenuStates.main_menu)
