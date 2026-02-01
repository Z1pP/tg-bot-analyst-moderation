from aiogram import F, Router
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.users_chats_settings import users_chats_settings_ikb
from utils.send_message import safe_edit_message

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.UserAndChatsSettings.SHOW_MENU)
async def users_chats_settings_handler(callback: CallbackQuery) -> None:
    """Обработчик нажатия на кнопку настроек пользователей и чатов"""
    await callback.answer()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.UserAndChatsSettings.MENU_TEXT,
        reply_markup=users_chats_settings_ikb(),
    )
