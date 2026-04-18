from dataclasses import dataclass

from aiogram.types import InlineKeyboardMarkup

from constants import Dialog
from keyboards.inline.chats import auto_moderation_setting_ikb, chats_menu_ikb
from services.chat import ChatService


@dataclass
class AutoModerationSettingsResult:
    """Данные для отображения настроек автомодерации."""

    text: str
    reply_markup: InlineKeyboardMarkup


class GetAutoModerationSettingsUseCase:
    """Подготавливает текст и клавиатуру раздела автомодерации."""

    def __init__(self, chat_service: ChatService) -> None:
        self._chat_service = chat_service

    async def execute(self, chat_id: int) -> AutoModerationSettingsResult:
        chat = await self._chat_service.get_chat_with_archive(chat_id=chat_id)
        if not chat:
            return AutoModerationSettingsResult(
                text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
                reply_markup=chats_menu_ikb(),
            )
        status = (
            "\U0001f7e2 Включена"
            if chat.is_auto_moderation_enabled
            else "\U0001f534 Выключена"
        )
        text = Dialog.AutoModeration.SETTINGS_INFO.format(
            chat_title=chat.title or "",
            status=status,
        )
        return AutoModerationSettingsResult(
            text=text,
            reply_markup=auto_moderation_setting_ikb(
                is_enabled=chat.is_auto_moderation_enabled
            ),
        )
