import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from keyboards.inline.message_actions import message_action_ikb
from states.admin_message_actions_states import AdminMessageActionsStates
from utils.data_parser import MESSAGE_LINK_PATTERN, parse_message_link
from utils.state_logger import log_and_set_state

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text.regexp(MESSAGE_LINK_PATTERN))
async def message_link_handler(message: types.Message, state: FSMContext) -> None:
    """Обработчик ссылки на сообщение."""
    result = parse_message_link(message.text)

    if not result:
        await message.reply("❌ Некорректная ссылка на сообщение")
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
        "🔧 <b>Действия с сообщением</b>\n\n"
        f"• ID сообщения: <code>{message_id}</code>\n"
        f"• Чат: <code>{chat_tgid}</code>\n\n"
        "Выберите действие:",
        reply_markup=message_action_ikb(),
    )
    await log_and_set_state(
        message, state, AdminMessageActionsStates.waiting_action_select
    )
