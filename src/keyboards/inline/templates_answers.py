from typing import List, Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models import MessageTemplate


def templates_inline_kb(
    templates: List[MessageTemplate],
    page: int = 1,
    total_count: int = 0,
    category_id: Optional[int] = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if not templates:
        builder.button(
            text="Шаблонов не найдено, создайте шаблон",
            callback_data="templates_not_found",
        )
        return builder.as_markup()

    # Добавляем кнопки шаблонов
    for index, template in enumerate(templates):
        builder.row(
            InlineKeyboardButton(
                text=f"{index + 1}. {template.title}",
                callback_data=f"template__{template.id}__{template.title}",
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"remove_template__{template.id}",
            ),
        )

    # Кнопки пагинации
    page_size = 5
    max_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    pagination_buttons = []

    # Кнопка "Назад"
    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(text="◀️", callback_data=f"prev_page__{page}")
        )
    else:
        pagination_buttons.append(
            InlineKeyboardButton(text="◀️", callback_data="no_prev")
        )

    # Информация о странице
    start_item = (page - 1) * page_size + 1
    end_item = min(page * page_size, total_count)
    pagination_buttons.append(
        InlineKeyboardButton(
            text=f"{start_item}-{end_item} из {total_count}", callback_data="page_info"
        )
    )

    # Кнопка "Вперед"
    if page < max_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text="▶️", callback_data=f"next_page__{page}")
        )
    else:
        pagination_buttons.append(
            InlineKeyboardButton(text="▶️", callback_data="no_next")
        )

    builder.row(*pagination_buttons)
    return builder.as_markup()


def conf_remove_template_kb() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Да",
            callback_data="conf_remove_template__yes",
        ),
        InlineKeyboardButton(
            text="Нет",
            callback_data="conf_remove_template__no",
        ),
        width=2,
    )
    return builder.as_markup()
