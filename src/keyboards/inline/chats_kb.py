from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models import AdminChatAccess, ChatSession


def remove_inline_kb(chats: list[ChatSession]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if not chats:
        builder.row(
            InlineKeyboardButton(
                text="Список чатов пуст. Добавьте бот в чат и выдайте ему админ права",
                callback_data="no_chat",
            )
        )
        return builder.as_markup()

    for index, chat in enumerate(chats):
        builder.row(
            InlineKeyboardButton(
                text=f"Удалить {chat.title[:30]}",
                callback_data=f"untrack_chat__{chat.id}",
            )
        )

    return builder.as_markup()


def chats_inline_kb(chats: list[ChatSession]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if not chats:
        builder.row(
            InlineKeyboardButton(
                text="Список чатов пуст. Добавьте бот в чат и выдайте ему админ права",
                callback_data="no_chat",
            )
        )
        return builder.as_markup()

    for index, chat in enumerate(chats):
        builder.row(
            InlineKeyboardButton(
                text=f"{index + 1}. {chat.title[:30]}",
                callback_data=f"chat__{chat.title}",
            )
        )

    return builder.as_markup()


def tracked_chats_inline_kb(chats: list[ChatSession]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if not chats:
        builder.row(
            InlineKeyboardButton(
                text="🚫 Нет отслеживаемых чатов",
                callback_data="no_tracked_chats",
            )
        )
        return builder.as_markup()

    for chat in chats:
        # Добавляем название чата
        builder.row(
            InlineKeyboardButton(
                text=f"Группа: {chat.title[:30]}",
                callback_data=f"chat_info__{chat.id}",
            )
        )

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


def chat_info_inline_kb(access: AdminChatAccess):
    builder = InlineKeyboardBuilder()

    if access.is_target:
        builder.row(
            InlineKeyboardButton(
                text="Не хочу получать отчеты сюда",
                callback_data=f"toggle_target__{access.chat_id}",
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="Хочу получать отчеты сюда",
                callback_data=f"toggle_target__{access.chat_id}",
            )
        ),

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="chat_info_back",
        ),
    )

    return builder.as_markup()
