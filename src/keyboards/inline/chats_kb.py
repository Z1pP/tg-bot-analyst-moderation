from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.chat_session import ChatSession


def chats_inline_kb(chats: list[ChatSession]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

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

        # Безопасное получение флагов
        if hasattr(chat, "admin_access") and chat.admin_access:
            admin_access = chat.admin_access[0]
            is_target = admin_access.is_target

        # Добавляем название чата
        builder.row(
            InlineKeyboardButton(
                text=f"Группа: {chat.title}", callback_data=f"chat_info__{chat.id}"
            )
        )

        builder.row(
            InlineKeyboardButton(
                text="✅ Отчеты включены" if is_target else "❌ Отчеты выключены",
                callback_data=f"toggle_target__{chat.id}",
            ),
        )

    return builder.as_markup()
