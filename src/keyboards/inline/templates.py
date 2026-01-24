from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.pagination import TEMPLATES_PAGE_SIZE
from models import MessageTemplate


def cancel_template_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.TemplateButtons.CANCEL,
            callback_data="cancel_template",
        )
    )
    return builder.as_markup()


def cancel_edit_ikb() -> InlineKeyboardMarkup:
    """Клавиатура для отмены редактирования названия или содержимого шаблона"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.TemplateButtons.CANCEL_EDIT,
            callback_data="cancel_edit_title_or_content",
        )
    )
    return builder.as_markup()


def templates_menu_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.TemplateButtons.SELECT_TEMPLATE,
            callback_data="select_template",
        ),
        InlineKeyboardButton(
            text=InlineButtons.TemplateButtons.SELECT_CATEGORY,
            callback_data="select_category",
        ),
        InlineKeyboardButton(
            text=InlineButtons.TemplateButtons.ADD_TEMPLATE,
            callback_data="add_template",
        ),
        InlineKeyboardButton(
            text=InlineButtons.TemplateButtons.ADD_CATEGORY,
            callback_data="add_category",
        ),
        width=2,
    )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Messages.BACK_TO_MESSAGE_MANAGEMENT,
            callback_data="message_management_menu",
        )
    )

    return builder.as_markup()


def templates_inline_kb(
    templates: List[MessageTemplate],
    page: int = 1,
    total_count: int = 0,
    page_size: int = TEMPLATES_PAGE_SIZE,
    show_back_to_categories: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки шаблонов
    for template in templates:
        # Кнопка с названием шаблона в отдельной строке для лучшей читаемости
        builder.row(
            InlineKeyboardButton(
                text=f"{template.title}",
                callback_data=f"template__{template.id}",
            )
        )
        # Кнопки действий под названием
        builder.row(
            InlineKeyboardButton(
                text="✏️", callback_data=f"edit_template__{template.id}"
            ),
            InlineKeyboardButton(
                text="🗑", callback_data=f"remove_template__{template.id}"
            ),
        )

    if total_count > page_size:
        max_pages = (total_count + page_size - 1) // page_size
        pagination_buttons = []

        # Кнопка "Назад"
        if page > 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="◀️", callback_data=f"prev_page__{page}")
            )

        # Информация о странице
        start_item = (page - 1) * page_size + 1
        end_item = min(page * page_size, total_count)
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"{start_item}-{end_item} из {total_count}",
                callback_data="page_info",
            )
        )

        # Кнопка "Вперед"
        if page < max_pages:
            pagination_buttons.append(
                InlineKeyboardButton(text="▶️", callback_data=f"next_page__{page}")
            )

        if pagination_buttons:
            builder.row(*pagination_buttons)

    # Кнопка возврата
    if show_back_to_categories:
        # Кнопка возврата к категориям
        builder.row(
            InlineKeyboardButton(
                text="⬅️ Вернуться к категориям",
                callback_data="select_category",
            )
        )
    else:
        # Кнопка возврата к списку чатов
        builder.row(
            InlineKeyboardButton(
                text="⬅️ Назад к выбору чата",
                callback_data="select_template",
            )
        )

    return builder.as_markup()


def edit_template_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✏️ Изменить название",
            callback_data="edit_title",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="📝 Изменить содержимое",
            callback_data="edit_content",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel_edit",
        )
    )

    return builder.as_markup()


def conf_remove_template_kb() -> InlineKeyboardMarkup:
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
