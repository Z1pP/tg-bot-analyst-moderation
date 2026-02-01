from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData
from constants.enums import UserRole


def role_select_ikb(user_id: int, current_role: UserRole) -> InlineKeyboardMarkup:
    """Клавиатура для выбора роли пользователя"""
    builder = InlineKeyboardBuilder()

    # Определяем текст для каждой роли с отметкой текущей роли
    admin_text = "👑 Администратор"
    moderator_text = "🛡️ Модератор"
    user_text = "👤 Пользователь"

    if current_role == UserRole.ADMIN:
        admin_text = "✅ " + admin_text
    elif current_role == UserRole.MODERATOR:
        moderator_text = "✅ " + moderator_text
    elif current_role == UserRole.USER:
        user_text = "✅ " + user_text

    # Кнопки для выбора роли
    builder.row(
        InlineKeyboardButton(
            text=admin_text,
            callback_data=f"{CallbackData.User.PREFIX_ROLE_SELECT}{user_id}__admin",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=moderator_text,
            callback_data=f"{CallbackData.User.PREFIX_ROLE_SELECT}{user_id}__moderator",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=user_text,
            callback_data=f"{CallbackData.User.PREFIX_ROLE_SELECT}{user_id}__user",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.Menu.MAIN_MENU,
        )
    )

    return builder.as_markup()


def cancel_role_select_ikb() -> InlineKeyboardMarkup:
    """Клавиатура для отмены выбора роли"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.Menu.MAIN_MENU,
        )
    )
    return builder.as_markup()
