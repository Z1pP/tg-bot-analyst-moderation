from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons, KbCommands
from constants.callback import CallbackData
from constants.pagination import CHATS_PAGE_SIZE
from dto import ChatDTO
from models import ChatSession


def remove_chat_ikb(
    chats: List[ChatSession],
    page: int = 1,
    total_count: int = 0,
    page_size: int = CHATS_PAGE_SIZE,
) -> InlineKeyboardMarkup:
    """Клавиатура для удаления чатов с пагинацией"""
    builder = InlineKeyboardBuilder()

    start_index = (page - 1) * page_size
    for index, chat in enumerate(chats):
        builder.row(
            InlineKeyboardButton(
                text=f"{start_index + index + 1}. Удалить {chat.title[:30]}",
                callback_data=f"{CallbackData.Chat.PREFIX_UNTRACK_CHAT}{chat.id}",
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

    # Кнопка возврата в меню (в самом низу)
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.ChatButtons.BACK_TO_CHATS_MENU,
            callback_data=CallbackData.Chat.CHATS_MENU,
        )
    )

    return builder.as_markup()


def tracked_chats_ikb(
    chats: List[ChatDTO],
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

    # Кнопка возврата в меню (в самом низу)
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.ChatButtons.BACK_TO_CHATS_MENU,
            callback_data="chats_menu",
        )
    )

    return builder.as_markup()


def tracked_chats_with_all_ikb(
    dtos: List[ChatDTO],
    page: int = 1,
    total_count: int = 0,
    page_size: int = CHATS_PAGE_SIZE,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if total_count > 1:
        # Кнопка "Все чаты" первой
        builder.row(
            InlineKeyboardButton(
                text="🌐 Все чаты",
                callback_data="chat__all",
            )
        )

    # Кнопки чатов
    start_index = (page - 1) * page_size
    for index, dto in enumerate(dtos):
        builder.row(
            InlineKeyboardButton(
                text=f"{start_index + index + 1}. {dto.title[:30]}",
                callback_data=f"chat__{dto.id}",
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


def template_scope_selector_ikb(chats: List[ChatSession]) -> InlineKeyboardMarkup:
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


def conf_remove_chat_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Да",
            callback_data=f"{CallbackData.Chat.PREFIX_CONFIRM_REMOVE_CHAT}yes",
        ),
        InlineKeyboardButton(
            text="Нет",
            callback_data=f"{CallbackData.Chat.PREFIX_CONFIRM_REMOVE_CHAT}no",
        ),
        width=2,
    )
    return builder.as_markup()


def select_chat_ikb(chats: List[ChatDTO]) -> InlineKeyboardMarkup:
    """Клавиатура для выбора чата для отправки сообщения."""
    builder = InlineKeyboardBuilder()

    for chat in chats:
        builder.row(
            InlineKeyboardButton(
                text=chat.title[:40],
                callback_data=f"select_chat_{chat.id}",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.MessageButtons.BACK_TO_MESSAGE_MANAGEMENT,
            callback_data="message_management_menu",
        )
    )

    return builder.as_markup()


def chat_actions_ikb() -> InlineKeyboardMarkup:
    """Клавиатура действий с выбранным чатом"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=KbCommands.GET_REPORT,
            callback_data=CallbackData.Chat.GET_REPORT,
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=KbCommands.DAILY_RATING,
            callback_data=CallbackData.Chat.GET_DAILY_RATING,
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=KbCommands.SELECT_CHAT,
            callback_data=CallbackData.Chat.SELECT_ANOTHER_CHAT,
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.ChatButtons.BACK_TO_CHATS_MENU,
            callback_data="chats_menu",
        )
    )

    return builder.as_markup()


def chats_menu_ikb() -> InlineKeyboardMarkup:
    """Клавиатура меню чатов"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=KbCommands.GET_STATISTICS,
            callback_data=CallbackData.Chat.GET_STATISTICS,
        ),
        InlineKeyboardButton(
            text=KbCommands.ADD_CHAT,
            callback_data=CallbackData.Chat.ADD,
        ),
        width=2,
    )

    builder.row(
        InlineKeyboardButton(
            text=KbCommands.REMOVE_CHAT,
            callback_data=CallbackData.Chat.REMOVE,
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.ChatButtons.BACK_TO_MAIN_MENU,
            callback_data=CallbackData.Chat.BACK_TO_MAIN_MENU,
        )
    )

    return builder.as_markup()
