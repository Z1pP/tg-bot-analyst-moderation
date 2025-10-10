from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from constants import KbCommands


def block_actions_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(text=KbCommands.AMNESTY),
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
