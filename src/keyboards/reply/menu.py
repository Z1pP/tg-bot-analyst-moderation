from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from constants import KbCommands


def admin_menu_kb():
    buttons = [
        [
            KeyboardButton(text=KbCommands.USERS_MENU),
            KeyboardButton(text=KbCommands.CHATS_MENU),
        ],
        [
            KeyboardButton(text=KbCommands.TEMPLATES_MENU),
        ],
        [
            KeyboardButton(text=KbCommands.SETTINGS),
            KeyboardButton(text=KbCommands.FAQ),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons, resize_keyboard=True, one_time_keyboard=True
    )


def tamplates_menu_kb():
    buttons = [
        [
            KeyboardButton(text=KbCommands.SELECT_TEMPLATE),
            KeyboardButton(text=KbCommands.SELECT_CATEGORY),
        ],
        [
            KeyboardButton(text=KbCommands.ADD_TEMPLATE),
            KeyboardButton(text=KbCommands.ADD_CATEGORY),
        ],
        [
            KeyboardButton(text=KbCommands.MENU),
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def moderator_menu_kb():
    buttons = [
        [
            KeyboardButton(text=KbCommands.SELECT_USER),
        ],
        [
            KeyboardButton(text=KbCommands.ADD_USER),
            KeyboardButton(text=KbCommands.REMOVE_USER),
        ],
        [
            KeyboardButton(text=KbCommands.MENU),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons, resize_keyboard=True, one_time_keyboard=True
    )


def chat_menu_kb():
    buttons = [
        [
            KeyboardButton(text=KbCommands.SELECT_CHAT),
        ],
        [
            KeyboardButton(text=KbCommands.ADD_CHAT),
            KeyboardButton(text=KbCommands.REMOVE_CHAT),
        ],
        # [
        #     KeyboardButton(text=KbCommands.TRACKED_CHATS),
        # ],
        [
            KeyboardButton(text=KbCommands.MENU),
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
