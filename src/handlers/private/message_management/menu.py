import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from keyboards.inline.message_actions import send_message_ikb
from states import MessageManagerState
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
