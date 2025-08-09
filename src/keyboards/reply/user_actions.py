from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from constants import KbCommands


def user_actions_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(text=KbCommands.GET_REPORT),
        ],
        [
            KeyboardButton(text=KbCommands.SELECT_USER),
        ],
        [
            KeyboardButton(text=KbCommands.MENU),
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def all_users_actions_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(text=KbCommands.FULL_REPORT),
        ],
        [
            KeyboardButton(text=KbCommands.SELECT_USER),
        ],
        [
            KeyboardButton(text=KbCommands.MENU),
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
