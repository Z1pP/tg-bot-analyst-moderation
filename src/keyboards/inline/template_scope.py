from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models import ChatSession


def template_scope_selection_kb(chats: List[ChatSession]) -> InlineKeyboardMarkup:
    """Клавиатура для выбора области шаблонов (глобальные или по чатам)"""
    builder = InlineKeyboardBuilder()
    
    # Кнопка для глобальных шаблонов
    builder.row(
        InlineKeyboardButton(
            text="🌐 Глобальные шаблоны",
            callback_data="template_scope_global",
        )
    )
    
    # Кнопки для каждого чата
    for chat in chats:
        builder.row(
            InlineKeyboardButton(
                text=f"💬 {chat.title[:30]}",
                callback_data=f"template_scope_chat__{chat.id}",
            )
        )
    
    return builder.as_markup()