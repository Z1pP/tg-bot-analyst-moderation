from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from constants import KbCommands


def chat_actions_kb(chat_title: str):
    chat_title = shorten(chat_title)
    buttons = [
        [
            KeyboardButton(text=KbCommands.SELECTED_CHAT.format(chat_title=chat_title)),
        ],
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
            KeyboardButton(text=KbCommands.MENU),
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def shorten(text: str, max_len: int = 25, suffix: str = "...") -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + suffix
