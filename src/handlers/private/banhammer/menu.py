import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.banhammer import moderation_menu_ikb
from states import ModerationStates
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.ModerationMenu.MENU)
async def lock_menu_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик меню блокировок через callback"""

    await callback.answer()
    await state.clear()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ModerationMenu.SELECT_ACTION,
        reply_markup=moderation_menu_ikb(),
    )

    await log_and_set_state(callback.message, state, ModerationStates.menu)
