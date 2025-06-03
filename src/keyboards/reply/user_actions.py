from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from constants import KbCommands


def get_user_actions_kb(username: str):
    buttons = [
        [
            KeyboardButton(text=KbCommands.SELECTED_USER.format(username=username)),
        ],
        [
            KeyboardButton(text=KbCommands.REPORT_RESPONSE_TIME),
        ],
        [
            KeyboardButton(text=KbCommands.MENU),
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=False)


def get_all_users_actions_kb():
    buttons = [
        [
            KeyboardButton(text=KbCommands.FULL_REPORT),
        ],
        [
            KeyboardButton(text=KbCommands.MENU),
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=False)
