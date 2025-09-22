from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants.pagination import CHATS_PAGE_SIZE
from models import ChatSession


def remove_inline_kb(
    chats: List[ChatSession],
    page: int = 1,
    total_count: int = 0,
    page_size: int = CHATS_PAGE_SIZE,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if not chats:
        builder.row(
            InlineKeyboardButton(
                text="Список чатов пуст. Добавьте бот в чат и выдайте ему админ права",
                callback_data="no_chat",
            )
        )
        return builder.as_markup()

    # Кнопки удаления чатов
    start_index = (page - 1) * page_size
    for index, chat in enumerate(chats):
        builder.row(
            InlineKeyboardButton(
                text=f"{start_index + index + 1}. Удалить {chat.title[:30]}",
                callback_data=f"untrack_chat__{chat.id}",
            )
        )

    # Пагинация
    if total_count > page_size:
        max_pages = (total_count + page_size - 1) // page_size
        pagination_buttons = []

        if page > 1:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="◀️", callback_data=f"prev_remove_chats_page__{page}"
                )
            )

        start_item = (page - 1) * page_size + 1
        end_item = min(page * page_size, total_count)
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"{start_item}-{end_item} из {total_count}",
                callback_data="remove_chats_page_info",
            )
        )

        if page < max_pages:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="▶️", callback_data=f"next_remove_chats_page__{page}"
                )
            )

        if pagination_buttons:
            builder.row(*pagination_buttons)

    return builder.as_markup()


def tracked_chats_inline_kb(
    chats: List[ChatSession],
    page: int = 1,
    total_count: int = 0,
    page_size: int = CHATS_PAGE_SIZE,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Кнопки чатов
    start_index = (page - 1) * page_size
    for index, chat in enumerate(chats):
        builder.row(
            InlineKeyboardButton(
                text=f"{start_index + index + 1}. {chat.title[:30]}",
                callback_data=f"chat__{chat.id}",
            )
        )

    # Пагинация
    if total_count > page_size:
        max_pages = (total_count + page_size - 1) // page_size
        pagination_buttons = []

        if page > 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="◀️", callback_data=f"prev_chats_page__{page}")
            )

        start_item = (page - 1) * page_size + 1
        end_item = min(page * page_size, total_count)
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"{start_item}-{end_item} из {total_count}",
                callback_data="chats_page_info",
            )
        )

        if page < max_pages:
            pagination_buttons.append(
                InlineKeyboardButton(text="▶️", callback_data=f"next_chats_page__{page}")
            )

        if pagination_buttons:
            builder.row(*pagination_buttons)

    return builder.as_markup()


def template_scope_selector_kb(chats: List[ChatSession]) -> InlineKeyboardMarkup:
    """Клавиатура для выбора области применения шаблона"""
    kb = InlineKeyboardBuilder()

    kb.button(
        text="🌐 Для всех чатов",
        callback_data="template_scope__-1",
    )

    # Добавляем доступные чаты
    for chat in chats:
        kb.button(
            text=f"💬 {chat.title[:30]}",
            callback_data=f"template_scope__{chat.id}",
        )

    # Формируем сетку 1 кнопка в ряд
    kb.adjust(1)
    return kb.as_markup()


def conf_remove_chat_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Да",
            callback_data="conf_remove_chat__yes",
        ),
        InlineKeyboardButton(
            text="Нет",
            callback_data="conf_remove_chat__no",
        ),
        width=2,
    )
    return builder.as_markup()
