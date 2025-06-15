from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.chat_session import ChatSession


def chats_inline_kb(chats: list[ChatSession]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Все чаты",
            callback_data="all_chats",
        )
    )

    for index, chat in enumerate(chats):
        builder.row(
            InlineKeyboardButton(
                text=f"{index + 1}. {chat.title}",
                callback_data=f"chat__{chat.title}",
            )
        )

    return builder.as_markup()


def tracked_chats_inline_kb(chats: list[ChatSession]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if not chats:
        builder.row(
            InlineKeyboardButton(
                text="🚫 Нет отслеживаемых чатов", callback_data="no_tracked_chats"
            )
        )
        return builder.as_markup()

    for chat in chats:
        is_target = False
        is_source = False

        # Безопасное получение флагов
        if hasattr(chat, "admin_access") and chat.admin_access:
            admin_access = chat.admin_access[0]
            is_target = admin_access.is_target
            is_source = admin_access.is_source

        # Добавляем название чата
        builder.row(
            InlineKeyboardButton(
                text=f"{chat.title}", callback_data=f"chat_info__{chat.id}"
            )
        )

        builder.row(
            InlineKeyboardButton(
                text="✅ Получатель" if is_target else "❌ Получатель",
                callback_data=f"toggle_target__{chat.id}",
            ),
            InlineKeyboardButton(
                text="✅ Источник" if is_source else "❌ Источник",
                callback_data=f"toggle_source__{chat.id}",
            ),
        )

    return builder.as_markup()
