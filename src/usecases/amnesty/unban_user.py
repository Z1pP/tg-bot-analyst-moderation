from typing import List, Optional

from exceptions.moderation import ArchiveChatError, BotInsufficientPermissionsError
from repositories import ChatRepository, UserChatStatusRepository
from services import BotMessageService, BotPermissionService, ChatService, UserService


class UnbanUserUseCase:
    def __init__(
        self,
        user_service: UserService,
        chat_service: ChatService,
        chat_repository: ChatRepository,
        bot_message_service: BotMessageService,
        bot_permission_service: BotPermissionService,
        user_chat_status_repository: UserChatStatusRepository,
    ):
        self.user_service = user_service
        self.chat_service = chat_service
        self.chat_repository = chat_repository
        self.bot_message_service = bot_message_service
        self.bot_permission_service = bot_permission_service
        self.user_chat_status_repository = user_chat_status_repository

    async def execute(
        self,
        admin_tgid: str,
        violator_tgid: str,
        chat_ids: Optional[List[int]] = None,
    ) -> List[str]:
        admin = await self.user_service.get_user(tg_id=admin_tgid)
        violator = await self.user_service.get_user(tg_id=violator_tgid)

        if not admin or not violator:
            return []

        if chat_ids is None:
            statuses = await self.user_chat_status_repository.get_all_by_user(
                user_id=violator.id
            )
            chat_ids = [status.chat_id for status in statuses if status.is_banned]

        unbanned_chats = []
        for chat_id in chat_ids:
            status = await self.user_chat_status_repository.get_status(
                user_id=violator.id, chat_id=chat_id
            )

            if status and status.is_banned:
                chat = await self.chat_repository.get_chat(chat_id=chat_id)
                if not chat:
                    continue

                can_moderate = await self.bot_permission_service.can_moderate(
                    chat_tgid=chat.chat_id
                )

                if not can_moderate:
                    raise BotInsufficientPermissionsError(chat_title=chat.title)

                archive_chats = await self.chat_service.get_archive_chats(
                    source_chat_title=chat.title
                )

                if not archive_chats:
                    raise ArchiveChatError()

                success = await self.bot_message_service.unban_chat_member(
                    chat_tg_id=chat.chat_id,
                    user_tg_id=int(violator_tgid),
                )

                if success:
                    updated_status = (
                        await self.user_chat_status_repository.update_status(
                            user_id=violator.id,
                            chat_id=chat_id,
                            is_banned=False,
                            is_muted=False,
                            muted_until=None,
                        )
                    )

                    if updated_status:
                        report_text = (
                            f"😇 Амнистия пользователя @{violator.username}\n"
                            f"• Разблокировал: @{admin.username}"
                        )

                        for archive_chat in archive_chats:
                            await self.bot_message_service.send_chat_message(
                                chat_tgid=archive_chat.chat_id,
                                text=report_text,
                            )

                        unbanned_chats.append(chat.title)

        return unbanned_chats
