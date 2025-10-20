from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from constants import KbCommands


def block_actions_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(text=KbCommands.AMNESTY),
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def amnesty_actions_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(text=KbCommands.CANCEL_WARN),
            KeyboardButton(text=KbCommands.UNMUTE),
            KeyboardButton(text=KbCommands.UNBAN),
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
