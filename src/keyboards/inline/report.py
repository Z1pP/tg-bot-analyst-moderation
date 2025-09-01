from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def order_details_kb(show_details: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if show_details:
        builder.row(
            InlineKeyboardButton(
                text="Заказать детализацию",
                callback_data="order_details",
            )
        )
    return builder.as_markup()
