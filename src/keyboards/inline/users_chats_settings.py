from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData


def users_chats_settings_ikb() -> InlineKeyboardMarkup:
    """Клавиатура настроек пользователей и чатов"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserAndChatsSettings.USERS_MENU,
            callback_data=CallbackData.User.SHOW_MENU,
        ),
        InlineKeyboardButton(
            text=InlineButtons.UserAndChatsSettings.CHATS_MENU,
            callback_data=CallbackData.Chat.SHOW_MENU,
        ),
        InlineKeyboardButton(
            text=InlineButtons.UserAndChatsSettings.RESET_SETTINGS,
            callback_data=CallbackData.UserAndChatsSettings.RESET_SETTINGS,
        ),
        InlineKeyboardButton(
            text=InlineButtons.UserAndChatsSettings.FIRST_TIME_SETTINGS,
            callback_data=CallbackData.UserAndChatsSettings.FIRST_TIME_SETTINGS,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Menu.SHOW_MENU,
        ),
    )

    builder.adjust(2, 1, 1, 1)

    return builder.as_markup()
