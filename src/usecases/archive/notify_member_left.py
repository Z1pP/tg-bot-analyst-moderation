import logging

from constants import Dialog
from dto import ArchiveMemberNotificationDTO
from services import ChatService
from services.messaging.bot_message_service import BotMessageService
from services.time_service import TimeZoneService

logger = logging.getLogger(__name__)


class NotifyArchiveChatMemberLeftUseCase:
    """
    UseCase для уведомления в архивный чат о выходе участника из группы.
    """

    def __init__(
        self,
        chat_service: ChatService,
        bot_message_service: BotMessageService,
    ) -> None:
        self.chat_service = chat_service
        self.bot_message_service = bot_message_service

    async def execute(self, dto: ArchiveMemberNotificationDTO) -> None:
        """
        Получает настройки чата и отправляет уведомление в архивный чат, если он привязан.

        Args:
            dto: DTO с данными для уведомления (chat_tgid, user_tgid, username, chat_title)
        """
        logger.info(
            "Попытка уведомления о выходе участника: chat_tgid=%s, user_tgid=%s, username=%s, chat_title=%s",
            dto.chat_tgid,
            dto.user_tgid,
            dto.username,
            dto.chat_title,
        )

        chat = await self.chat_service.get_chat_with_archive(chat_tgid=dto.chat_tgid)

        if chat is None:
            logger.info(
                "Чат %s не найден в БД. Уведомление о выходе участника %s пропущено.",
                dto.chat_tgid,
                dto.user_tgid,
            )
            return

        if not chat.archive_chat_id:
            logger.info(
                "Для чата %s (%s) не привязан архив. Уведомление о выходе участника %s пропущено.",
                dto.chat_tgid,
                dto.chat_title,
                dto.user_tgid,
            )
            return

        now = TimeZoneService.now()
        date_str = now.strftime("%d.%m.%Y")
        time_str = now.strftime("%H:%M")

        username_display = f"@{dto.username}" if dto.username else "Отсутствует"

        report_text = Dialog.ArchiveNotification.MEMBER_LEFT.format(
            username=username_display,
            tg_id=dto.user_tgid,
            date=date_str,
            time=time_str,
            chat_title=dto.chat_title,
        )

        await self.bot_message_service.send_chat_message(
            chat_tgid=chat.archive_chat_id,
            text=report_text,
        )

        logger.info(
            "Отправлено уведомление о выходе участника %s в архивный чат %s для чата %s",
            dto.user_tgid,
            chat.archive_chat_id,
            dto.chat_tgid,
        )
