import logging

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from constants import Dialog
from dto.automoderation import SpamDetectionLLMResultDTO
from keyboards.inline.automoderation import automoderation_alert_ikb
from services.messaging.bot_message_service import BotMessageService
from utils.telegram_links import public_group_message_link

logger = logging.getLogger(__name__)


class NotifyAutoModerationHitUseCase:
    """Формирует HTML и отправляет уведомление с кнопками в архив."""

    def __init__(self, bot_message_service: BotMessageService) -> None:
        self._bot_message_service = bot_message_service

    async def execute(
        self,
        *,
        work_chat_tgid: str,
        work_chat_title: str,
        archive_chat_tgid: str,
        detection: SpamDetectionLLMResultDTO,
    ) -> None:
        violator_line = (
            f"@{detection.username}"
            if detection.username
            else Dialog.AutoModeration.NO_USERNAME
        )
        message_url = public_group_message_link(work_chat_tgid, detection.message_id)
        text = Dialog.AutoModeration.ALERT_BODY.format(
            violator_line=violator_line,
            user_tg_id=detection.user_tg_id,
            reason=detection.reason,
            chat_title=work_chat_title,
            message_url=message_url,
        )
        try:
            await self._bot_message_service.send_chat_message(
                chat_tgid=archive_chat_tgid,
                text=text,
                reply_markup=automoderation_alert_ikb(
                    work_chat_tgid, detection.user_tg_id
                ),
            )
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.warning(
                "automod: не удалось отправить карточку в архив %s: %s",
                archive_chat_tgid,
                e,
            )
        except (OSError, TimeoutError) as e:
            logger.error(
                "automod: сеть при отправке в архив %s: %s",
                archive_chat_tgid,
                e,
                exc_info=True,
            )
