from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import RELEASE_NOTES_ADMIN_IDS, Dialog
from constants.callback import CallbackData
from constants.i18n import DEFAULT_LANGUAGE, get_text


def admin_menu_ikb(
    user_language: str = None,
    admin_tg_id: Optional[str] = None,
) -> InlineKeyboardMarkup:
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
    release_notes_text = get_text("RELEASE_NOTES", user_language)

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=users_menu_text,
            callback_data=CallbackData.Menu.USERS_MENU,
        ),
        InlineKeyboardButton(
            text=Dialog.Chat.CHATS_MENU,
            callback_data=CallbackData.Menu.CHATS_MENU,
        ),
        width=2,
    )

    builder.row(
        InlineKeyboardButton(
            text=Dialog.MessageManager.MESSAGE_MANAGEMENT,
            callback_data=CallbackData.Menu.MESSAGE_MANAGEMENT,
        ),
        InlineKeyboardButton(
            text=Dialog.BlockMenu.LOCK_MENU,
            callback_data=CallbackData.Menu.LOCK_MENU,
        ),
        width=2,
    )

    # Добавляем кнопку для просмотра логов действий администраторов
    # (только для авторизованных пользователей)
    if admin_tg_id and admin_tg_id in RELEASE_NOTES_ADMIN_IDS:
        builder.row(
            InlineKeyboardButton(
                text=Dialog.AdminLogs.ADMIN_LOGS,
                callback_data=CallbackData.AdminLogs.MENU,
            ),
            InlineKeyboardButton(
                text=Dialog.Roles.PERMISSIONS_MENU,
                callback_data=CallbackData.Permissions.MENU,
            ),
            width=2,
        )

    builder.row(
        InlineKeyboardButton(
            text=release_notes_text,
            callback_data=CallbackData.ReleaseNotes.MENU,
        ),
    )

    return builder.as_markup()
