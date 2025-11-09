from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from dto import ChatDTO


def template_scope_selection_ikb(chats: List[ChatDTO]) -> InlineKeyboardMarkup:
    """Keyboard for selecting where to add templates"""
    builder = InlineKeyboardBuilder()

    # all chats selection button
    builder.row(
        InlineKeyboardButton(
            text="🌐 Для всех чатов",
            callback_data="template_scope_global",
        )
    )

    # button for selecting a specific chat
    for chat in chats:
        builder.row(
            InlineKeyboardButton(
                text=f"💬 {chat.title[:30]}",
                callback_data=f"template_scope_chat__{chat.id}",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.TemplateButtons.BACK_TO_TEMPLATES_MENU,
            callback_data="templates_menu",
        )
    )

    return builder.as_markup()
