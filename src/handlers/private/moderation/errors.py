import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.inline.moderation import moderation_menu_ikb
from states.moderation import ModerationStates
from utils.send_message import safe_edit_message

logger = logging.getLogger(__name__)


async def handle_chats_error(
    callback: CallbackQuery,
    state: FSMContext,
    violator_username: str,
    error: Exception = None,
) -> None:
    """Обрабатывает ошибки получения чатов."""
    if error:
        logger.error("Ошибка получения чатов: %s", error, exc_info=True)
        text = "❌️ Произошла ошибка при получении списка чатов. Попробуйте еще раз."
    else:
        text = (
            f"❌️ Мы не нашли чатов, где @{violator_username} получил ограничение. "
            "Перепроверьте введённые данные, либо попробуйте снять ограничение вручную."
        )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=moderation_menu_ikb(),
    )

    await state.set_state(ModerationStates.menu)
