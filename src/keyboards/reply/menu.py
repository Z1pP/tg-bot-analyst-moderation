from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from constants import KbCommands


def admin_menu_kb():
    buttons = [
        [
            KeyboardButton(text=KbCommands.SELECT_MODERATOR),
            KeyboardButton(text=KbCommands.SELECT_CHAT),
        ],
        [
            KeyboardButton(text=KbCommands.ADD_MODERATOR),
            KeyboardButton(text=KbCommands.REMOVE_MODERATOR),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons, resize_keyboard=True, one_time_keyboard=True
    )


def get_back_kb():
    buttons = [
        [
            KeyboardButton(text=KbCommands.BACK),
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons, resize_keyboard=True, one_time_keyboard=True
    )
