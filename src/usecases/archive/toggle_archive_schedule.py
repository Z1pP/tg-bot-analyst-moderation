"""Use case: переключение рассылки отчётов в архив."""

from __future__ import annotations

import logging
from typing import Optional

from constants import Dialog
from dto.chat_dto import GetChatWithArchiveDTO
from keyboards.inline.chats import archive_channel_setting_ikb
from services.messaging import BotMessageService
from services.report_schedule_service import ReportScheduleService
from usecases.chat import GetChatWithArchiveUseCase
from utils.archive import build_schedule_info

from .get_archive_settings import ArchiveSettingsResult

logger = logging.getLogger(__name__)


class ToggleArchiveScheduleUseCase:
    """Переключает вкл/выкл рассылки отчётов и возвращает данные для обновления UI."""

    def __init__(
        self,
        get_chat_with_archive: GetChatWithArchiveUseCase,
        report_schedule_service: ReportScheduleService,
        bot_message_service: BotMessageService,
    ) -> None:
        self._get_chat = get_chat_with_archive
        self._schedule_service = report_schedule_service
        self._bot_message_service = bot_message_service

    async def execute(self, chat_id: int) -> Optional[ArchiveSettingsResult]:
        """
        Переключает расписание и возвращает текст + клавиатуру для сообщения.
        Возвращает None при ошибке (чат не найден, расписание не найдено и т.д.).
        """
        schedule = await self._schedule_service.get_schedule(chat_id=chat_id)
        if not schedule:
            return None

        new_enabled = not schedule.enabled
        updated_schedule = await self._schedule_service.toggle_schedule(
            chat_id=chat_id, enabled=new_enabled
        )
        if not updated_schedule:
            return None

        chat = await self._get_chat.execute(GetChatWithArchiveDTO(chat_id=chat_id))
        if not chat or not chat.archive_chat:
            return None

        schedule_info, schedule_enabled = build_schedule_info(updated_schedule)
        text = Dialog.Chat.ARCHIVE_CHANNEL_EXISTS.format(
            title=chat.title, schedule_info=schedule_info
        )

        invite_link = await self._bot_message_service.get_chat_invite_link(
            chat_tgid=chat.archive_chat.chat_id
        )

        return ArchiveSettingsResult(
            text=text,
            reply_markup=archive_channel_setting_ikb(
                archive_chat=chat.archive_chat or None,
                invite_link=invite_link,
                schedule_enabled=schedule_enabled,
            ),
        )
