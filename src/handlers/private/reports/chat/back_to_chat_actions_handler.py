import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import chat_actions_ikb
from states import ChatStateManager
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == CallbackData.Chat.BACK_TO_CHAT_ACTIONS,
    ChatStateManager.selecting_period,
)
async def back_to_chat_actions_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик возврата к действиям с чатом из выбора периода."""
    await callback.answer()

    logger.info(
        "Пользователь %s возвращается к действиям с чатом",
        callback.from_user.id,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.CHAT_MANAGEMENT,
        reply_markup=chat_actions_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=ChatStateManager.selecting_chat,
    )
