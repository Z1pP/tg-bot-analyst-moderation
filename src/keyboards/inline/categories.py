from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models import QuickResponseCategory


def categories_inline_kb(
    categories: list[QuickResponseCategory],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if not categories:
        builder.row(
            InlineKeyboardButton(
                text="Категорий не найдено, создайте категорию",
                callback_data="categories_not_found",
            )
        )
        return builder.as_markup()

    for index, category in enumerate(categories):
        builder.row(
            InlineKeyboardButton(
                text=f"{index + 1}. {category.name}",
                callback_data=f"category__{category.id}",
            )
        )

    return builder.as_markup()
