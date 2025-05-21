from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from constants import KbCommands


def get_moderators_list_kb():
    buttons = [
        [
            KeyboardButton(text=KbCommands.GET_MODERATORS_LIST),
        ],
        [
            KeyboardButton(text=KbCommands.ADD_MODERATOR),
            KeyboardButton(text=KbCommands.REMOVE_MODERATOR),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons, resize_keyboard=True, one_time_keyboard=True
    )
