from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.pagination import CATEGORIES_PAGE_SIZE
from models import TemplateCategory


def cancel_category_ikb() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для отмены действия над категорией."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data="cancel_category",
        )
    )
    return builder.as_markup()


def confirmation_add_category_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.TemplateButtons.CONFIRM_ADD,
            callback_data="conf_add_category",
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL, callback_data="cancel_category"
        ),
    )
    return builder.as_markup()


def confirmation_edit_category_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.TemplateButtons.CONFIRM_SAVE,
            callback_data="conf_edit_category",
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL, callback_data="cancel_category"
        ),
    )
    return builder.as_markup()


def categories_inline_ikb(
    categories: List[TemplateCategory],
    page: int = 1,
    total_count: int = 0,
    page_size: int = CATEGORIES_PAGE_SIZE,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
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

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data="templates_menu",
        )
    )

    return builder.as_markup()


def categories_select_only_ikb(
    categories: List[TemplateCategory],
    page: int = 1,
    total_count: int = 0,
    page_size: int = CATEGORIES_PAGE_SIZE,
) -> InlineKeyboardMarkup:
    """Клавиатура для выбора категории при добавлении шаблона (только названия, без кнопок редактирования/удаления)"""
    builder = InlineKeyboardBuilder()
    for category in categories:
        # Только кнопка с названием категории
        builder.row(
            InlineKeyboardButton(
                text=f"{category.name}",
                callback_data=f"category__{category.id}",
            )
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

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data="templates_menu",
        )
    )

    return builder.as_markup()


def conf_remove_category_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.TemplateButtons.CONFIRM_REMOVE,
            callback_data="conf_remove_category",
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data="cancel_remove_category",
        ),
        width=2,
    )
    return builder.as_markup()
