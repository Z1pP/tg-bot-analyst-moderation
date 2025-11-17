import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from keyboards.inline.chats_kb import chat_actions_ikb
from states import ChatStateManager
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "back_to_chat_actions")
async def back_to_chat_actions_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик возврата к действиям с чатом из выбора периода."""
    await callback.answer()

    data = await state.get_data()
    chat_id = data.get("chat_id")

    logger.info(
        "Пользователь %s начал возврат к действиям с чатом %s",
        callback.from_user.username,
        chat_id,
    )

    if not chat_id:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Report.SELECT_CHAT_AGAIN,
            reply_markup=chat_actions_ikb(),
        )
        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=ChatStateManager.selecting_chat,
        )
        return

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=ChatStateManager.selecting_chat,
    )
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.SELECT_ACTION,
        reply_markup=chat_actions_ikb(),
    )
