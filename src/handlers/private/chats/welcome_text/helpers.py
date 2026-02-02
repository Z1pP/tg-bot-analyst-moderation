from aiogram.types import InlineKeyboardMarkup

from constants import Dialog
from keyboards.inline.chats import welcome_text_setting_ikb
from models import ChatSession


def build_welcome_text_view(chat: ChatSession) -> tuple[str, InlineKeyboardMarkup]:
    antibot_status = "🟢 Включён" if chat.is_antibot_enabled else "🔴 Выключен"
    welcome_text_status = "🟢 Включён" if chat.show_welcome_text else "🔴 Выключен"
    auto_delete_status = (
        "🟢 Включён" if chat.auto_delete_welcome_text else "🔴 Выключен"
    )

    text = Dialog.Chat.WELCOME_TEXT_INFO.format(
        chat_title=chat.title,
        antibot_status=antibot_status,
        welcome_text_status=welcome_text_status,
        auto_delete_status=auto_delete_status,
    )
    reply_markup = welcome_text_setting_ikb(
        welcome_text_enabled=chat.show_welcome_text,
        auto_delete_enabled=chat.auto_delete_welcome_text,
    )
    return text, reply_markup
