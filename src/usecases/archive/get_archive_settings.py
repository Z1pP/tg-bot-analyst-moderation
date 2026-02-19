"""Usecase for building archive settings view."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from aiogram.types import InlineKeyboardMarkup

from constants import Dialog
from exceptions.base import BotBaseException
from keyboards.inline.chats import archive_channel_setting_ikb, chats_menu_ikb
from dto import GetChatWithArchiveDTO
from services import ChatService
from services.messaging import BotMessageService
from services.permissions import BotPermissionService
from services.report_schedule_service import ReportScheduleService
from utils.archive import build_schedule_info

logger = logging.getLogger(__name__)


@dataclass
class ArchiveSettingsResult:
    """Result for archive settings view."""

    text: str
    reply_markup: InlineKeyboardMarkup


class GetArchiveSettingsUseCase:
    """UseCase for preparing archive settings view data."""

    def __init__(
        self,
        chat_service: ChatService,
        bot_permission_service: BotPermissionService,
        report_schedule_service: ReportScheduleService,
        bot_message_service: BotMessageService,
    ) -> None:
        self._chat_service = chat_service
        self._bot_permission_service = bot_permission_service
        self._report_schedule_service = report_schedule_service
        self._bot_message_service = bot_message_service

    async def execute(self, dto: GetChatWithArchiveDTO) -> ArchiveSettingsResult:
        """Build archive settings view for chat."""
        try:
            chat = await self._chat_service.get_chat_with_archive(
                chat_id=dto.chat_id,
                chat_tgid=dto.chat_tgid,
            )
        except BotBaseException:
            raise
        except Exception as exc:
            logger.exception("Ошибка при получении чата: %s", exc)
            raise BotBaseException(
                message=Dialog.Chat.ERROR_GET_CHAT_WITH_ARCHIVE,
                details={"original": str(exc)},
            ) from exc

        if not chat:
            return ArchiveSettingsResult(
                text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
                reply_markup=chats_menu_ikb(),
            )

        if chat.archive_chat:
            permissions_check = (
                await self._bot_permission_service.check_archive_permissions(
                    chat_tgid=chat.archive_chat.chat_id
                )
            )

            if not permissions_check.has_all_permissions:
                permissions_list = "\n".join(
                    f"• {perm}" for perm in permissions_check.missing_permissions
                )
                error_text = Dialog.Chat.ARCHIVE_INSUFFICIENT_PERMISSIONS.format(
                    title=chat.archive_chat.title,
                    permissions_list=permissions_list,
                )
                return ArchiveSettingsResult(
                    text=error_text,
                    reply_markup=archive_channel_setting_ikb(
                        archive_chat=chat.archive_chat or None,
                        invite_link=None,
                        schedule_enabled=False,
                    ),
                )

            schedule = await self._report_schedule_service.get_schedule(
                chat_id=chat.id
            )
            schedule_info, schedule_enabled = build_schedule_info(schedule)
            text = Dialog.Chat.ARCHIVE_CHANNEL_EXISTS.format(
                title=chat.title,
                schedule_info=schedule_info,
            )

            invite_link = await self._bot_message_service.get_chat_invite_link(
                chat_tgid=chat.archive_chat.chat_id
            )
        else:
            text = Dialog.Chat.ARCHIVE_CHANNEL_MISSING.format(title=chat.title)
            invite_link = None
            schedule_enabled = None

        return ArchiveSettingsResult(
            text=text,
            reply_markup=archive_channel_setting_ikb(
                archive_chat=chat.archive_chat or None,
                invite_link=invite_link,
                schedule_enabled=schedule_enabled,
            ),
        )
