from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models import TemplateCategory


def categories_inline_kb(
    categories: list[TemplateCategory],
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
            ),
            InlineKeyboardButton(
                text="🗑 Удалить",
                callback_data=f"remove_category__{category.id}",
            ),
            width=2,
        )

    return builder.as_markup()


def conf_remove_category_kb() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Да",
            callback_data="conf_remove_category__yes",
        ),
        InlineKeyboardButton(
            text="Нет",
            callback_data="conf_remove_category__no",
        ),
        width=2,
    )
    return builder.as_markup()
