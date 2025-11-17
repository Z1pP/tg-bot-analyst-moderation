from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from constants import KbCommands
from constants.i18n import DEFAULT_LANGUAGE, get_text


def admin_menu_kb(user_language: str = None):
    """
    Создает клавиатуру главного меню администратора с учетом языка пользователя.

    Args:
        user_language: Код языка пользователя (например, 'ru', 'en')
    """
    if user_language is None:
        user_language = DEFAULT_LANGUAGE

    users_menu_text = get_text("USERS_MENU", user_language)

    buttons = [
        [
            KeyboardButton(text=users_menu_text),
            KeyboardButton(text=KbCommands.CHATS_MENU),
        ],
        [
            KeyboardButton(text=KbCommands.MESSAGE_MANAGEMENT),
            KeyboardButton(text=KbCommands.LOCK_MENU),
        ],
        [
            # KeyboardButton(text=KbCommands.SETTINGS),
            # KeyboardButton(text=KbCommands.FAQ),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons, resize_keyboard=True, one_time_keyboard=True
    )
