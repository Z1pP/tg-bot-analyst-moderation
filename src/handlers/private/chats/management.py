from aiogram import F, Router
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import chats_menu_ikb
from utils.send_message import safe_edit_message

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.Chat.MANAGEMENT)
async def chats_management_handler(callback: CallbackQuery):
    """Обработчик меню управления чатами"""
    await callback.answer()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.SELECT_ACTION,
        reply_markup=chats_menu_ikb(
            has_tracked_chats=False,
            callback_data=CallbackData.Analytics.SHOW_MENU,
        ),
    )
