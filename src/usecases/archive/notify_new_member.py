import logging

from constants import Dialog
from services import ChatService
from services.messaging.bot_message_service import BotMessageService
from services.time_service import TimeZoneService

logger = logging.getLogger(__name__)


class NotifyArchiveChatNewMemberUseCase:
    """
    UseCase для уведомления в архивный чат о новом участнике.
    """

    def __init__(
        self,
        chat_service: ChatService,
        bot_message_service: BotMessageService,
    ):
        self.chat_service = chat_service
        self.bot_message_service = bot_message_service

    async def execute(
        self,
        chat_tgid: str,
        user_tgid: int,
        username: str,
        chat_title: str,
    ) -> None:
        """
        Получает настройки чата и отправляет уведомление в архивный чат, если он привязан.

        Args:
            chat_tgid: Telegram ID рабочего чата
            user_tgid: Telegram ID нового пользователя
            username: Username нового пользователя
            chat_title: Название рабочего чата
        """
        chat = await self.chat_service.get_chat_with_archive(chat_tgid=chat_tgid)

        if not chat or not chat.archive_chat_id:
            logger.debug(
                "Для чата %s не привязан архивный чат. Уведомление о новом участнике пропущено.",
                chat_tgid,
            )
            return

        now = TimeZoneService.now()
        date_str = now.strftime("%d.%m.%Y")
        time_str = now.strftime("%H:%M")

        username_display = f"@{username}" if username else "Отсутствует"

        report_text = Dialog.ArchiveNotification.NEW_MEMBER.format(
            username=username_display,
            tg_id=user_tgid,
            date=date_str,
            time=time_str,
            chat_title=chat_title,
        )

        await self.bot_message_service.send_chat_message(
            chat_tgid=chat.archive_chat_id,
            text=report_text,
        )

        logger.info(
            "Отправлено уведомление о новом участнике %s в архивный чат %s для чата %s",
            user_tgid,
            chat.archive_chat_id,
            chat_tgid,
        )
