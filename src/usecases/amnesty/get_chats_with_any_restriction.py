from typing import List, Optional

from dto import AmnestyUserDTO, ChatDTO
from repositories import (
    ChatTrackingRepository,
    PunishmentRepository,
    UserChatStatusRepository,
)
from services import BotPermissionService, UserService

from .base_get_chats import BaseGetChatsUseCase


class GetChatsWithAnyRestrictionUseCase(BaseGetChatsUseCase):
    """Возвращает чаты где у пользователя есть любые ограничения (бан, мут, преды)."""

    def __init__(
        self,
        user_service: UserService,
        chat_tracking_repository: ChatTrackingRepository,
        user_chat_status_repository: UserChatStatusRepository,
        punishment_repository: PunishmentRepository,
        bot_permission_service: BotPermissionService,
    ):
        super().__init__(user_service, chat_tracking_repository)
        self.user_chat_status_repository = user_chat_status_repository
        self.punishment_repository = punishment_repository
        self.bot_permission_service = bot_permission_service

    async def execute(self, dto: AmnestyUserDTO) -> Optional[List[ChatDTO]]:
        async def has_any_restriction(chat):
            # 1. Проверяем наличие предупреждений в БД
            count = await self.punishment_repository.count_punishments(
                user_id=dto.violator_id,
                chat_id=chat.id,
            )
            if count > 0:
                return True

            # 2. Проверяем статус в БД (бан или мут)
            status = await self.user_chat_status_repository.get_status(
                user_id=dto.violator_id,
                chat_id=chat.id,
            )
            if status and (status.is_banned or status.is_muted):
                return True

            # 3. Проверяем фактический статус в Telegram
            try:
                member_status = (
                    await self.bot_permission_service.get_chat_member_status(
                        user_tgid=int(dto.violator_tgid),
                        chat_tgid=chat.chat_id,
                    )
                )
                if member_status.is_banned or member_status.is_muted:
                    return True
            except Exception:
                pass

            return False

        return await super().execute(dto, has_any_restriction)
