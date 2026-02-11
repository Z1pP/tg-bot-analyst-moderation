from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData


def root_menu_ikb() -> InlineKeyboardMarkup:
    """Клавиатура для root-меню"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Roles.MENU,
            callback_data=CallbackData.Roles.INPUT_USER_DATA,
        ),
        InlineKeyboardButton(
            text=InlineButtons.AdminLogs.MENU,
            callback_data=CallbackData.Root.SHOW_MENU,
        ),
        InlineKeyboardButton(
            text=InlineButtons.ReleaseNotes.MENU,
            callback_data=CallbackData.ReleaseNotes.MENU,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Menu.SHOW_MENU,
        ),
    )
    builder.adjust(1, 2, 1)
    return builder.as_markup()
