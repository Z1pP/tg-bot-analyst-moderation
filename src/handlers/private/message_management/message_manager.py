import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog, KbCommands
from keyboards.inline.message_actions import send_message_ikb
from keyboards.reply.menu import admin_menu_kb
from states import MenuStates, MessageManagerState
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(F.text == KbCommands.MESSAGE_MANAGEMENT)
async def message_management_handler(message: types.Message, state: FSMContext) -> None:
    logger.info(
        "Администратор %s выбрал пункт %s",
        message.from_user.username,
        KbCommands.MESSAGE_MANAGEMENT,
    )

    sent_message = await message.answer(
        text=Dialog.MessageManager.INPUT_MESSAGE_LINK,
        reply_markup=send_message_ikb(),
    )

    # Сохраняем message_id для последующего редактирования
    await state.update_data(active_message_id=sent_message.message_id)

    await log_and_set_state(message, state, MessageManagerState.waiting_message_link)

    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение: {e}")


@router.callback_query(F.data == "message_management_menu")
async def message_management_menu_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик возврата в меню управления сообщениями."""
    await callback.answer()

    logger.info(
        "Администратор %s вернулся в меню управления сообщениями",
        callback.from_user.username,
    )

    await callback.message.edit_text(
        text=Dialog.MessageManager.INPUT_MESSAGE_LINK,
        reply_markup=send_message_ikb(),
    )

    # Сохраняем message_id для последующего редактирования
    await state.update_data(active_message_id=callback.message.message_id)

    await log_and_set_state(
        callback.message, state, MessageManagerState.waiting_message_link
    )


@router.callback_query(F.data == "back_to_main_menu_from_message_management")
async def back_to_main_menu_from_message_management_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик возврата в главное меню из меню управления сообщениями"""
    await callback.answer()
    await state.clear()

    username = callback.from_user.first_name
    menu_text = Dialog.MENU_TEXT.format(username=username)

    await callback.message.answer(
        text=menu_text,
        reply_markup=admin_menu_kb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=MenuStates.main_menu,
    )

    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение меню управления сообщениями: {e}")
