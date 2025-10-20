import logging

from constants.punishment import PunishmentType
from dto import AmnestyUserDTO, CancelWarnResultDTO
from exceptions.moderation import ArchiveChatError, BotInsufficientPermissionsError
from repositories import (
    PunishmentRepository,
    PunishmentLadderRepository,
    UserChatStatusRepository,
)
from services import BotMessageService, BotPermissionService, ChatService
from utils.formatter import format_duration

logger = logging.getLogger(__name__)


class CancelLastWarnUseCase:
    def __init__(
        self,
        bot_message_service: BotMessageService,
        bot_permission_service: BotPermissionService,
        punishment_repository: PunishmentRepository,
        punishment_ladder_repository: PunishmentLadderRepository,
        user_chat_status_repository: UserChatStatusRepository,
        chat_service: ChatService,
    ):
        self.bot_message_service = bot_message_service
        self.bot_permission_service = bot_permission_service
        self.punishment_repository = punishment_repository
        self.punishment_ladder_repository = punishment_ladder_repository
        self.user_chat_status_repository = user_chat_status_repository
        self.chat_service = chat_service

    async def execute(self, dto: AmnestyUserDTO) -> CancelWarnResultDTO:
        current_count = 0
        next_ladder = None

        for chat in dto.chat_dtos:
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

            deleted = await self.punishment_repository.delete_last_punishment(
                user_id=dto.violator_id, chat_id=chat.id
            )

            if not deleted:
                logger.warning("Не найдено наказаний для отмены в чате %s", chat.id)
                continue

            current_count = await self.punishment_repository.count_punishments(
                user_id=dto.violator_id, chat_id=chat.id
            )

            next_ladder = (
                await self.punishment_ladder_repository.get_punishment_by_step(
                    step=current_count + 1,
                    chat_id=chat.tg_id,
                )
            )

            if current_count == 0:
                await self.user_chat_status_repository.reset_status(
                    user_id=dto.violator_id, chat_id=chat.id
                )
                # Снимаем все ограничения в Telegram
                await self.bot_message_service.unban_chat_member(
                    chat_tg_id=chat.tg_id,
                    user_tg_id=int(dto.violator_tgid),
                )
            else:
                current_ladder = (
                    await self.punishment_ladder_repository.get_punishment_by_step(
                        step=current_count,
                        chat_id=chat.tg_id,
                    )
                )
                if current_ladder:
                    # Получаем текущий статус пользователя
                    current_status = await self.user_chat_status_repository.get_status(
                        user_id=dto.violator_id, chat_id=chat.id
                    )

                    was_banned = current_status.is_banned if current_status else False
                    was_muted = current_status.is_muted if current_status else False

                    # Обновляем статус в БД
                    await self.user_chat_status_repository.update_status(
                        user_id=dto.violator_id,
                        chat_id=chat.id,
                        is_banned=current_ladder.punishment_type == PunishmentType.BAN,
                        is_muted=current_ladder.punishment_type == PunishmentType.MUTE,
                    )

                    # Применяем или снимаем ограничения в Telegram
                    if current_ladder.punishment_type == PunishmentType.BAN:
                        # Применяем бан
                        await self.bot_message_service.ban_chat_member(
                            chat_tg_id=chat.tg_id,
                            user_tg_id=int(dto.violator_tgid),
                        )
                    elif current_ladder.punishment_type == PunishmentType.MUTE:
                        # Проверяем статус пользователя в чате
                        try:
                            member = await self.bot_message_service.bot.get_chat_member(
                                chat_id=chat.tg_id,
                                user_id=int(dto.violator_tgid),
                            )
                            # Если пользователь забанен или покинул чат, сначала разбаниваем
                            if member.status in ["kicked", "left"]:
                                await self.bot_message_service.unban_chat_member(
                                    chat_tg_id=chat.tg_id,
                                    user_tg_id=int(dto.violator_tgid),
                                )
                        except Exception as e:
                            logger.warning(
                                "Не удалось проверить статус пользователя %s в чате %s: %s",
                                dto.violator_tgid,
                                chat.tg_id,
                                e,
                            )

                        # Применяем мут с новой длительностью
                        await self.bot_message_service.mute_chat_member(
                            chat_tg_id=chat.tg_id,
                            user_tg_id=int(dto.violator_tgid),
                            duration_seconds=current_ladder.duration_seconds,
                        )
                    else:
                        # Текущее наказание - WARNING, снимаем все ограничения
                        if was_banned:
                            await self.bot_message_service.unban_chat_member(
                                chat_tg_id=chat.tg_id,
                                user_tg_id=int(dto.violator_tgid),
                            )
                        elif was_muted:
                            await self.bot_message_service.unmute_chat_member(
                                chat_tg_id=chat.tg_id,
                                user_tg_id=int(dto.violator_tgid),
                            )
                else:
                    await self.user_chat_status_repository.reset_status(
                        user_id=dto.violator_id, chat_id=chat.id
                    )
                    await self.bot_message_service.unban_chat_member(
                        chat_tg_id=chat.tg_id,
                        user_tg_id=int(dto.violator_tgid),
                    )

            if next_ladder and next_ladder.punishment_type == PunishmentType.BAN:
                next_step = "бессрочная блокировка."
            elif next_ladder and next_ladder.punishment_type == PunishmentType.MUTE:
                next_step = f"мут на {format_duration(next_ladder.duration_seconds)}."
            else:
                next_step = "предупреждение."

            report_text = (
                f"⏪ <b>Отмена последнего предупреждения для @{dto.violator_username}</b>\n\n"
                f"• Отменил: @{dto.admin_username} в чате <b>{chat.title}</b>\n"
                f"• След. шаг: {next_step}"
            )

            for archive_chat in archive_chats:
                await self.bot_message_service.send_chat_message(
                    chat_tgid=archive_chat.chat_id,
                    text=report_text,
                )

            logger.info(
                "Отменено последнее предупреждение для пользователя %s в чате %s",
                dto.violator_username,
                chat.id,
            )

        return CancelWarnResultDTO(
            success=True,
            current_warns_count=current_count,
            next_punishment_type=next_ladder.punishment_type if next_ladder else None,
            next_punishment_duration=(
                next_ladder.duration_seconds if next_ladder else None
            ),
        )
