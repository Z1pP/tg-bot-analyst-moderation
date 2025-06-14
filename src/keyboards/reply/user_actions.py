from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from constants import KbCommands


def user_actions_kb(username: str):
    buttons = [
        [
            KeyboardButton(text=KbCommands.SELECTED_USER.format(username=username)),
        ],
        [
            KeyboardButton(text=KbCommands.GET_REPORT),
        ],
        [
            KeyboardButton(text=KbCommands.SELECT_MODERATOR),
        ],
        [
            KeyboardButton(text=KbCommands.MENU),
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def all_users_actions_kb():
    buttons = [
        [
            KeyboardButton(text=KbCommands.FULL_REPORT),
        ],
        [
            KeyboardButton(text=KbCommands.SELECT_MODERATOR),
        ],
        [
            KeyboardButton(text=KbCommands.MENU),
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
