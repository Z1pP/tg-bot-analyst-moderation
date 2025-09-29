import logging
from datetime import timedelta

from dto import ModerationActionDTO
from models.punishment_ladder import PunishmentType
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


class GiveUserWarnUseCase(ModerationUseCase):
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

        punishment_count = await self.punishment_service.get_punishment_count(
            user_id=context.violator.id,
        )
        punishment = await self.punishment_service.get_punishment(
            warn_count=punishment_count,
            chat_id=context.dto.chat_tgid,
        )

        if not punishment:
            logger.info(
                "Пользователь %s уже прошел все шаги наказания в чате %s.",
                context.violator.username,
                context.dto.chat_title,
            )
            text = (
                f"Пользователь @{context.violator.username} уже прошел все шаги наказания в чате "
                f"{context.dto.chat_title}. Дальнейшие автоматические наказания невозможны. "
                f"Примите меры вручную."
            )
            await self.bot_message_service.send_private_message(
                user_tgid=context.dto.admin_tgid, text=text
            )
            return

        new_punishment = await self.punishment_service.create_punishment(
            user=context.violator,
            punishment=punishment,
            admin_id=context.admin.id,
            chat_id=context.chat.id,
        )

        correct_date = TimeZoneService.convert_to_local_time(
            dt=new_punishment.created_at
        )

        report = self.punishment_service.generate_report(
            dto=context.dto,
            punishment=punishment,
            date=correct_date,
        )

        reason_text = self.punishment_service.generate_reason_for_user(
            punishment_type=punishment.punishment_type,
            duration_of_punishment=punishment.duration_seconds,
            punished_username=context.violator.username,
        )

        await self._finalize_moderation(
            context=context,
            report_text=report,
            reason_text=reason_text,
        )

        if punishment.punishment_type == PunishmentType.MUTE:
            await self.bot_message_service.mute_chat_member(
                chat_id=context.dto.chat_tgid,
                user_id=context.dto.user_reply_tgid,
                until_date=timedelta(seconds=punishment.duration_seconds),
            )

            until_date = correct_date + timedelta(
                seconds=punishment.duration_seconds,
            )
            await self.user_chat_status_repository.update_status(
                user_id=context.violator.id,
                chat_id=context.chat.id,
                is_muted=True,
                muted_until=until_date,
            )

        if punishment.punishment_type == PunishmentType.BAN:
            await self.bot_message_service.ban_chat_member(
                chat_id=context.dto.chat_tgid,
                user_id=context.dto.user_reply_tgid,
            )
            await self.user_chat_status_repository.update_status(
                user_id=context.violator.id,
                chat_id=context.chat.id,
                is_banned=True,
            )
