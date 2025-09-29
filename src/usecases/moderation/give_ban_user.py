import logging

from constants.punishment import PunishmentText
from dto import ModerationActionDTO
from repositories.user_chat_status_repository import UserChatStatusRepository
from services import (
    BotMessageService,
    ChatService,
    PunishmentService,
    UserService,
)
from services.time_service import TimeZoneService

from .base import ModerationUseCase

logger = logging.getLogger(__name__)


class GiveUserBanUseCase(ModerationUseCase):
    def __init__(
        self,
        user_service: UserService,
        bot_message_service: BotMessageService,
        chat_service: ChatService,
        punishment_service: PunishmentService,
        user_chat_status_repository: UserChatStatusRepository,
    ):
        super().__init__(
            user_service,
            bot_message_service,
            chat_service,
            user_chat_status_repository,
        )
        self.punishment_service = punishment_service

    async def execute(self, dto: ModerationActionDTO) -> None:
        context = await self._prepare_moderation_context(dto=dto)

        if not context:
            return

        await self.bot_message_service.ban_chat_member(
            chat_id=context.dto.chat_tgid,
            user_id=context.dto.user_reply_tgid,
        )

        await self.user_chat_status_repository.update_status(
            user_id=context.violator.id,
            chat_id=context.chat.id,
            is_banned=True,
        )

        correct_date = TimeZoneService.now()

        report_text = self.punishment_service.generate_ban_report(
            dto=context.dto,
            date=correct_date,
        )

        reason_text = PunishmentText.BAN.value.format(
            username=context.dto.user_reply_username
        )

        await self._finalize_moderation(
            context=context,
            report_text=report_text,
            reason_text=reason_text,
        )
