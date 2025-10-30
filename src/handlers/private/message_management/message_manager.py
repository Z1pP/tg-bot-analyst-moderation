import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from states import MessageManagerState
from utils.state_logger import log_and_set_state

from constants import KbCommands, Dialog


router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(F.text == KbCommands.MESSAGE_MANAGEMENT)
async def message_management_handler(message: types.Message, state: FSMContext) -> None:
    logger.info(
        "Администратор %s выбрал пункт %s",
        message.from_user.username,
        KbCommands.MESSAGE_MANAGEMENT,
    )

    await message.answer(text=Dialog.MessageManager.INPUT_MESSAGE_LINK)
    await log_and_set_state(message, state, MessageManagerState.waiting_message_link)
