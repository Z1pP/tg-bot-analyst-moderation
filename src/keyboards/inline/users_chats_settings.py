from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData


def users_chats_settings_ikb(has_tracking: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура настроек пользователей и чатов"""
    builder = InlineKeyboardBuilder()

    if has_tracking:
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.UserAndChatsSettings.USERS_MENU,
                callback_data=CallbackData.User.SHOW_MENU,
            ),
            InlineKeyboardButton(
                text=InlineButtons.UserAndChatsSettings.CHATS_MENU,
                callback_data=CallbackData.Chat.SHOW_MENU,
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.UserAndChatsSettings.RESET_SETTINGS,
                callback_data=CallbackData.UserAndChatsSettings.RESET_SETTINGS,
            ),
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.UserAndChatsSettings.FIRST_TIME_SETTINGS,
                callback_data=CallbackData.UserAndChatsSettings.FIRST_TIME_SETTINGS,
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Menu.SHOW_MENU,
        ),
    )

    return builder.as_markup()


def confirm_reset_ikb() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения сброса настроек"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.YES,
            callback_data=CallbackData.UserAndChatsSettings.CONFIRM_RESET,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.NO,
            callback_data=CallbackData.UserAndChatsSettings.CANCEL_RESET,
        ),
    )

    return builder.as_markup()


def reset_success_ikb() -> InlineKeyboardMarkup:
    """Клавиатура успешного сброса настроек"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserAndChatsSettings.START_FIRST_TIME_SETTINGS,
            callback_data=CallbackData.UserAndChatsSettings.FIRST_TIME_SETTINGS,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.UserAndChatsSettings.SHOW_MENU,
        )
    )

    return builder.as_markup()
