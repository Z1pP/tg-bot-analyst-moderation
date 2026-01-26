from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import Dialog, InlineButtons
from constants.callback import CallbackData


def analytics_menu_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=Dialog.User.SHOW_TRACKED_USERS,
            callback_data=CallbackData.User.SELECT_USER_FOR_ANALYTICS,
        ),
        InlineKeyboardButton(
            text=Dialog.Chat.SHOW_TRACKED_CHATS,
            callback_data=CallbackData.Chat.SELECT_CHAT_FOR_REPORT,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Menu.SHOW_MENU,
        ),
    )

    builder.adjust(2, 1)
    return builder.as_markup()
