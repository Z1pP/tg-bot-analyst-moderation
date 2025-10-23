from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


def message_action_ikb() -> types.InlineKeyboardMarkup:
    """Клавиатура с действиями над сообщением."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data="delete_message",
        ),
        types.InlineKeyboardButton(
            text="💬 Ответить",
            callback_data="reply_message",
        ),
    )
    builder.row(
        types.InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel",
        ),
    )
    return builder.as_markup()


def confirm_delete_ikb() -> types.InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data="delete_message_confirm",
        ),
        types.InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="delete_message_cancel",
        ),
    )
    return builder.as_markup()
