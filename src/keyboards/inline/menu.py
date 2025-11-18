from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import KbCommands
from constants.callback import CallbackData
from constants.i18n import DEFAULT_LANGUAGE, get_text


def admin_menu_ikb(user_language: str = None) -> InlineKeyboardMarkup:
    """
    Создает inline клавиатуру главного меню администратора с учетом языка пользователя.

    Args:
        user_language: Код языка пользователя (например, 'ru', 'en')

    Returns:
        InlineKeyboardMarkup: Inline клавиатура главного меню
    """
    if user_language is None:
        user_language = DEFAULT_LANGUAGE

    users_menu_text = get_text("USERS_MENU", user_language)

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=users_menu_text,
            callback_data=CallbackData.Menu.USERS_MENU,
        ),
        InlineKeyboardButton(
            text=KbCommands.CHATS_MENU,
            callback_data=CallbackData.Menu.CHATS_MENU,
        ),
        width=2,
    )

    builder.row(
        InlineKeyboardButton(
            text=KbCommands.MESSAGE_MANAGEMENT,
            callback_data=CallbackData.Menu.MESSAGE_MANAGEMENT,
        ),
        InlineKeyboardButton(
            text=KbCommands.LOCK_MENU,
            callback_data=CallbackData.Menu.LOCK_MENU,
        ),
        width=2,
    )

    return builder.as_markup()
