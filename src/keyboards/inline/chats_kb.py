from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models import AdminChatAccess, ChatSession


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
        # Добавляем название чата
        builder.row(
            InlineKeyboardButton(
                text=f"Группа: {chat.title}", callback_data=f"chat_info__{chat.id}"
            )
        )

    return builder.as_markup()


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
