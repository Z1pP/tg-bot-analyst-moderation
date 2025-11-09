import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from keyboards.inline.message_actions import message_action_ikb
from states.message_management import MessageManagerState
from utils.data_parser import MESSAGE_LINK_PATTERN, parse_message_link
from utils.state_logger import log_and_set_state

router = Router()
logger = logging.getLogger(__name__)


@router.message(
    F.text.regexp(MESSAGE_LINK_PATTERN),
    MessageManagerState.waiting_message_link,
)
async def message_link_handler(message: types.Message, state: FSMContext) -> None:
    """Обработчик ссылки на сообщение."""
    result = parse_message_link(message.text)

    if not result:
        await message.reply(Dialog.MessageManager.INVALID_LINK)
        return

    chat_tgid, message_id = result

    logger.info(
        "Админ %s запросил действия для сообщения %s в чате %s",
        message.from_user.id,
        message_id,
        chat_tgid,
    )

    await state.update_data(
        chat_tgid=chat_tgid,
        message_id=message_id,
    )

    await message.reply(
        Dialog.MessageManager.MESSAGE_ACTIONS.format(
            message_id=message_id,
            chat_tgid=chat_tgid,
        ),
        reply_markup=message_action_ikb(),
    )
    await log_and_set_state(message, state, MessageManagerState.waiting_action_select)
