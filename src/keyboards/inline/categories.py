from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants.pagination import CATEGORIES_PAGE_SIZE
from models import TemplateCategory


def categories_inline_kb(
    categories: List[TemplateCategory],
    page: int = 1,
    total_count: int = 0,
    page_size: int = CATEGORIES_PAGE_SIZE,
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

    # Кнопки категорий
    for category in categories:
        # Кнопка с названием категории в отдельной строке
        builder.row(
            InlineKeyboardButton(
                text=f"{category.name}",
                callback_data=f"category__{category.id}",
            )
        )
        # Кнопки действий под названием
        builder.row(
            InlineKeyboardButton(
                text="✏️",
                callback_data=f"edit_category__{category.id}",
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"remove_category__{category.id}",
            ),
        )

    # Пагинация (только если больше одной страницы)
    if total_count > page_size:
        max_pages = (total_count + page_size - 1) // page_size
        pagination_buttons = []

        # Кнопка "Назад"
        if page > 1:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="◀️", callback_data=f"prev_categories_page__{page}"
                )
            )

        # Информация о странице
        start_item = (page - 1) * page_size + 1
        end_item = min(page * page_size, total_count)
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"{start_item}-{end_item} из {total_count}",
                callback_data="categories_page_info",
            )
        )

        # Кнопка "Вперед"
        if page < max_pages:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="▶️", callback_data=f"next_categories_page__{page}"
                )
            )

        if pagination_buttons:
            builder.row(*pagination_buttons)

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
