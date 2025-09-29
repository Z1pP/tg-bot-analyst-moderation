from datetime import datetime
from typing import Optional

from constants.punishment import PunishmentText
from dto import ModerationActionDTO
from models import Punishment, User
from models.punishment_ladder import PunishmentLadder, PunishmentType
from repositories import PunishmentLadderRepository, PunishmentRepository
from utils.formatter import format_seconds


class PunishmentService:
    def __init__(
        self,
        punishment_repository: PunishmentRepository,
        punishment_ladder_repository: PunishmentLadderRepository,
    ):
        self.punishment_repository = punishment_repository
        self.punishment_ladder_repository = punishment_ladder_repository

    def generate_reason_for_user(
        self,
        duration_of_punishment: int,
        punished_username: str,
        punishment_type: PunishmentType = PunishmentType.WARNING,
    ) -> str:
        """
        Возвращает текст наказания для пользователя в зависимости от типа наказания.
        """
        punishment_text_template = PunishmentText[punishment_type.name].value

        if punishment_type == PunishmentType.MUTE:
            period = format_seconds(seconds=duration_of_punishment)
            return PunishmentText.MUTE.format(username=punished_username, period=period)

        return punishment_text_template.format(username=punished_username)

    async def get_punishment_count(self, user_id: int) -> int:
        return await self.punishment_repository.get_punishment_count(user_id)

    async def get_punishment(
        self,
        warn_count: int,
        chat_id: str,
    ) -> Optional[PunishmentLadder]:
        return await self.punishment_ladder_repository.get_punishment_by_step(
            step=warn_count + 1,
            chat_id=chat_id,
        )

    def generate_report(
        self,
        dto: ModerationActionDTO,
        punishment: PunishmentLadder,
        date: datetime,
    ) -> str:
        date_str = date.strftime("%d.%m.%Y")
        time_str = date.strftime("%H:%M")
        reason = dto.reason or "Не указана"
        period = ""

        if punishment.punishment_type == PunishmentType.BAN:
            period = "бессрочно"
        elif punishment.punishment_type == PunishmentType.MUTE:
            period = format_seconds(seconds=punishment.duration_seconds)

        mute_line = f"• Время мута: {period}\n" if period else ""

        return (
            f"❌️ Сообщение удалено {date_str} в {time_str}\n\n"
            f"• Юзер: @{dto.user_reply_username}\n"
            f"• ID: {dto.user_reply_tgid}\n"
            f"• Причина: {reason}\n"
            f"{mute_line}"
            f"• Выдал пред: @{dto.admin_username}\n"
            f"• Чат: {dto.chat_title}"
        )

    async def create_punishment(
        self,
        user: User,
        punishment: PunishmentLadder,
        admin_id: int,
        chat_id: str,
    ) -> Punishment:
        new_punishment = Punishment(
            user_id=user.id,
            step=punishment.step,
            punishment_type=punishment.punishment_type,
            duration_seconds=punishment.duration_seconds,
            punished_by_id=admin_id,
            chat_id=chat_id,
        )
        return await self.punishment_repository.create_punishment(new_punishment)
