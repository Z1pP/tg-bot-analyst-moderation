from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from constants import KbCommands


def chat_actions_kb():
    buttons = [
        [
            KeyboardButton(text=KbCommands.GET_REPORT),
        ],
        [
            KeyboardButton(text=KbCommands.SELECT_CHAT),
        ],
        [
            KeyboardButton(text=KbCommands.MENU),
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def all_chats_actions_kb():
    buttons = [
        [
            KeyboardButton(text=KbCommands.FULL_REPORT),
        ],
        [
            KeyboardButton(text=KbCommands.SELECT_CHAT),
        ],
        [
            KeyboardButton(text=KbCommands.TRACKED_CHATS),
        ],
        [
            KeyboardButton(text=KbCommands.MENU),
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
