import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from keyboards.inline.message_actions import confirm_delete_ikb
from states.message_management import MessageManagerState
from utils.state_logger import log_and_set_state

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(
    MessageManagerState.waiting_action_select,
    F.data.in_(["delete_message", "reply_message", "cancel"]),
)
async def message_action_select_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик выбора действия с сообщением."""
    await callback.answer()

    if callback.data == "delete_message":
        await callback.message.edit_text(
            Dialog.MessageManagerDialogs.DELETE_CONFIRM,
            reply_markup=confirm_delete_ikb(),
        )
        await log_and_set_state(
            callback.message, state, MessageManagerState.waiting_delete_confirm
        )
        logger.info("Админ %s запросил удаление сообщения", callback.from_user.id)

    elif callback.data == "reply_message":
        await callback.message.edit_text(Dialog.MessageManagerDialogs.REPLY_INPUT)
        await log_and_set_state(
            callback.message, state, MessageManagerState.waiting_reply_message
        )
        logger.info("Админ %s запросил ответ на сообщение", callback.from_user.id)

    elif callback.data == "cancel":
        await callback.message.edit_text(Dialog.MessageManagerDialogs.ACTION_CANCELLED)
        await state.clear()
        logger.info("Админ %s отменил действие", callback.from_user.id)
