import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog, KbCommands
from keyboards.inline.message_actions import send_message_ikb
from states import MessageManagerState
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
