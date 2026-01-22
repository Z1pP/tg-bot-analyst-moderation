"""Usecase for antibot settings view."""

from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import InlineKeyboardMarkup

from constants import Dialog
from keyboards.inline.chats import antibot_setting_ikb, chats_management_ikb
from services.chat import ChatService


@dataclass
class AntibotSettingsResult:
    """Result for antibot settings view."""

    text: str
    reply_markup: InlineKeyboardMarkup


class GetAntibotSettingsUseCase:
    """UseCase for preparing antibot settings view data."""

    def __init__(self, chat_service: ChatService) -> None:
        self._chat_service = chat_service

    async def execute(self, chat_id: int) -> AntibotSettingsResult:
        """Build antibot settings view for chat."""
        chat = await self._chat_service.get_chat_with_archive(chat_id=chat_id)

        if not chat:
            return AntibotSettingsResult(
                text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
                reply_markup=chats_management_ikb(),
            )

        antibot_status = "🟢 Включён" if chat.is_antibot_enabled else "🔴 Выключен"
        welcome_text_status = "🟢 Включён" if chat.show_welcome_text else "🔴 Выключен"

        text = Dialog.Antibot.SETTINGS_INFO.format(
            chat_title=chat.title,
            antibot_status=antibot_status,
            welcome_text_status=welcome_text_status,
        )

        return AntibotSettingsResult(
            text=text,
            reply_markup=antibot_setting_ikb(is_enabled=chat.is_antibot_enabled),
        )
