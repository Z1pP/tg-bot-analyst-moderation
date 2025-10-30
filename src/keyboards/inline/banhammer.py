from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def no_reason_ikb() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой 'Без причины'."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="❌ Без причины",
            callback_data="no_reason",
        )
    )
    return builder.as_markup()
