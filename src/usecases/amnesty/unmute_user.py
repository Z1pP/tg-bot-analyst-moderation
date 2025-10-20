from typing import List, Optional

from exceptions.moderation import ArchiveChatError, BotInsufficientPermissionsError
from repositories import UserChatStatusRepository
from services import (
    BotMessageService,
    BotPermissionService,
    ChatService,
)
from dto import AmnestyUserDTO


class UnmuteUserUseCase:
    def __init__(
        self,
        bot_message_service: BotMessageService,
        bot_permission_service: BotPermissionService,
        user_chat_status_repository: UserChatStatusRepository,
        chat_service: ChatService = ChatService,
    ):
        self.bot_message_service = bot_message_service
        self.bot_permission_service = bot_permission_service
        self.user_chat_status_repository = user_chat_status_repository
        self.chat_service = chat_service

    async def execute(self, dto: AmnestyUserDTO) -> None:
        for chat in dto.chat_dtos:
            # Проверяем что имеет необходимые права
            can_moderate = await self.bot_permission_service.can_moderate(
                chat_tgid=chat.tg_id
            )

            if not can_moderate:
                raise BotInsufficientPermissionsError(chat_title=chat.title)

            archive_chats = await self.chat_service.get_archive_chats(
                source_chat_tgid=chat.tg_id,
            )

            if not archive_chats:
                raise ArchiveChatError(chat_title=chat.title)

            success = await self.bot_message_service.unmute_chat_member(
                chat_tg_id=chat.tg_id,
                user_tg_id=int(dto.violator_tgid),
            )

            if success:
                await self.user_chat_status_repository.update_status(
                    user_id=dto.violator_id,
                    chat_id=chat.id,
                    is_muted=False,
                    muted_until=None,
                )

                report_text = (
                    f"🔊 Размут пользователя @{dto.violator_username}\n\n"
                    f"• Размутил: @{dto.admin_username} в чате <b>{chat.title}</b>"
                )

                for archive_chat in archive_chats:
                    await self.bot_message_service.send_chat_message(
                        chat_tgid=archive_chat.chat_id,
                        text=report_text,
                    )
