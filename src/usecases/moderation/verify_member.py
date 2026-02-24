import logging
from typing import Optional

from constants import Dialog
from constants.punishment import PunishmentType
from dto import ResultVerifyMember
from repositories import (
    PunishmentLadderRepository,
)
from services import (
    BotMessageService,
    BotPermissionService,
    ChatService,
    PunishmentService,
)
from services.user import UserService
from utils.formatter import format_duration

logger = logging.getLogger(__name__)


def _format_next_punishment_description(
    punishment_type: PunishmentType,
    duration_seconds: Optional[int],
) -> str:
    """Формирует описание следующего наказания для сообщения пользователю."""
    if punishment_type == PunishmentType.WARNING:
        return "предупреждение"
    if punishment_type == PunishmentType.MUTE and duration_seconds:
        return f"мут {format_duration(duration_seconds)}"
    if punishment_type == PunishmentType.BAN:
        return "бан"
    return "предупреждение"


class VerifyMemberUseCase:
    """
    UseCase для верификации пользователя через нажатие кнопки в групповом чате.
    """

    def __init__(
        self,
        bot_message_service: BotMessageService,
        bot_permission_service: BotPermissionService,
        chat_service: ChatService,
        user_service: UserService,
        punishment_service: PunishmentService,
        punishment_ladder_repository: PunishmentLadderRepository,
    ):
        self.bot_message_service = bot_message_service
        self.bot_permission_service = bot_permission_service
        self.chat_service = chat_service
        self.user_service = user_service
        self.punishment_service = punishment_service
        self.punishment_ladder_repository = punishment_ladder_repository

    async def execute(
        self,
        user_tgid: str,
        chat_tgid: str,
    ) -> ResultVerifyMember:
        """
        Проверяет наличие наказаний; при их отсутствии снимает мут с пользователя
        прошедшего антибот-верификацию.

        Args:
            user_id: Telegram ID верифицированного пользователя
            chat_id: Telegram ID чата

        Returns:
            ResultVerifyMember с флагом unmuted и готовым сообщением для callback.answer
        """
        can_moderate = await self.bot_permission_service.can_moderate(
            chat_tgid=chat_tgid
        )
        if not can_moderate:
            logger.warning(
                "Бот не имеет прав модератора в чате %s. Невозможно размутить пользователя %s.",
                chat_tgid,
                user_tgid,
            )
            return ResultVerifyMember(
                unmuted=False,
                message="Не удалось выполнить проверку. Нет прав модератора в чате.",
            )

        chat = await self.chat_service.get_chat(chat_tgid=chat_tgid)
        if chat is None:
            logger.warning(
                "Чат %s не найден в БД при верификации пользователя %s.",
                chat_tgid,
                user_tgid,
            )
            return ResultVerifyMember(
                unmuted=False,
                message="Не удалось выполнить проверку. Чат не найден.",
            )

        user = await self.user_service.get_user(tg_id=user_tgid)

        count = 0
        if user is not None:
            count = await self.punishment_service.get_punishment_count(
                user_id=user.id,
                chat_id=chat.id,
            )

        if count > 0:
            next_ladder = (
                await self.punishment_ladder_repository.get_punishment_by_step(
                    step=count + 1,
                    chat_id=chat.chat_id,
                )
            )
            if next_ladder:
                next_desc = _format_next_punishment_description(
                    next_ladder.punishment_type,
                    next_ladder.duration_seconds,
                )
            else:
                next_desc = "предупреждение"
            message = Dialog.Antibot.VERIFIED_HAS_PUNISHMENTS.format(
                warns_count=count,
                next_punishment_description=next_desc,
            )
            logger.info(
                "У пользователя %s в чате %s есть наказания (count=%s), мут не снимаем.",
                user_tgid,
                chat_tgid,
                count,
            )
            return ResultVerifyMember(unmuted=False, message=message)

        success = await self.bot_message_service.unmute_chat_member(
            chat_tg_id=chat_tgid,
            user_tg_id=user_tgid,
        )

        if success:
            logger.info(
                "Пользователь %s успешно прошел антибот-верификацию в чате %s",
                user_tgid,
                chat_tgid,
            )
            return ResultVerifyMember(
                unmuted=True,
                message=Dialog.Antibot.VERIFIED_SUCCESS,
            )

        return ResultVerifyMember(
            unmuted=False,
            message="Не удалось снять ограничения. Попробуйте позже.",
        )
