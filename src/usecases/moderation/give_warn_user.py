import logging
from datetime import timedelta

from dto import ModerationActionDTO
from models.punishment_ladder import PunishmentType
from services import (
    BotMessageService,
    ChatService,
    PunishmentService,
    UserService,
)
from services.time_service import TimeZoneService

logger = logging.getLogger(__name__)


class GiveUserWarnUseCase:
    def __init__(
        self,
        user_service: UserService,
        bot_message_service: BotMessageService,
        chat_service: ChatService,
        punishment_service: PunishmentService,
    ):
        self.user_service = user_service
        self.bot_message_service = bot_message_service
        self.chat_service = chat_service
        self.punishment_service = punishment_service

    async def execute(self, dto: ModerationActionDTO) -> None:
        if self.is_different_sender(dto=dto) is False:
            logger.info(
                "Попытка выдать предупреждение самому себе от %s c ID=%s",
                dto.admin_username,
                dto.admin_tgid,
            )
            return

        # Получаем список чатов куда будут сохранться отчеты о наказаниях
        archive_chats = await self.chat_service.get_archive_chats(
            source_chat_title=dto.chat_title,
        )

        if not archive_chats:
            text = (
                "Пожалуйста, создайте рабочий чат с историей удалённых сообщений и"
                " добавьте его в Аналиста. В будущем это облегчит работу при поиске "
                "заблокированных пользователей."
            )

            # Отправляем сообщение админу в ЛС о необходимости создать архивный чат
            await self.bot_message_service.send_private_message(
                user_tgid=dto.admin_tgid,
                text=text,
            )

            # Также рассылаем всем админам, у которых этот чат is_tracked, сообщение
            # о необходимости создать архивный чат
            await self.send_messages_to_admins(
                dto=dto,
                text=text,
            )

            return

        # Получаем нарушителя и админа из БД
        violator = await self.user_service.get_user(tg_id=dto.user_reply_tgid)
        admin = await self.user_service.get_user(tg_id=dto.admin_tgid)

        # Получаем чат из БД
        chat = await self.chat_service.get_chat(title=dto.chat_title)

        # Получаем информацию и количестве нарушений у пользователя
        punishment_count = await self.punishment_service.get_punishment_count(
            user_id=violator.id
        )

        # Получаем информацию, какое наказание должно быть принято к нарушителю
        # исходя из числа прошлых нарушений и исходя из списка наказаний для данного
        # чата
        punishment = await self.punishment_service.get_punishment(
            warn_count=punishment_count,
            chat_id=dto.chat_tgid,
        )

        if not punishment:
            logger.info(
                "Пользователь %s уже прошел все шаги наказания в чате %s.",
                violator.username,
                dto.chat_title,
            )
            text = (
                f"Пользователь @{violator.username} уже прошел все шаги наказания в чате "
                f"{dto.chat_title}. Дальнейшие автоматические наказания невозможны. "
                f"Примите меры вручную."
            )
            await self.bot_message_service.send_private_message(
                user_tgid=dto.admin_tgid,
                text=text,
            )
            return

        new_punishment = await self.punishment_service.create_punishment(
            user=violator,
            punishment=punishment,
            admin_id=admin.id,
            chat_id=dto.chat_tgid,
        )

        correct_date = TimeZoneService.convert_to_local_time(
            dt=new_punishment.created_at
        )

        # Создаем отчет
        report = self.punishment_service.generate_report(
            dto=dto,
            punishment=punishment,
            date=correct_date,
        )

        # Отправляем отчет о наказании по архивным чатам
        for chat in archive_chats:
            await self.bot_message_service.forward_message(
                chat_tgid=chat.chat_id,
                from_chat_tgid=dto.chat_tgid,
                message_tgid=dto.reply_message_id,
            )
            await self.bot_message_service.send_chat_message(
                chat_tgid=chat.chat_id,
                text=report,
            )

        # Генерируем текст "наказания" согласно типу наказания полученного из БД
        reason_text = self.punishment_service.generate_reason_for_user(
            punishment_type=punishment.punishment_type,
            duration_of_punishment=punishment.duration_seconds,
            punished_username=violator.username,
        )

        await self.bot_message_service.delete_message_from_chat(
            chat_id=dto.chat_tgid,
            message_id=dto.reply_message_id,
        )

        await self.bot_message_service.send_chat_message(
            chat_tgid=dto.chat_tgid,
            text=reason_text,
        )

        if punishment.punishment_type == PunishmentType.MUTE:
            await self.bot_message_service.mute_chat_member(
                chat_id=dto.chat_tgid,
                user_id=dto.user_reply_tgid,
                until_date=timedelta(seconds=punishment.duration_seconds),
            )

        if punishment.punishment_type == PunishmentType.BAN:
            await self.bot_message_service.ban_chat_member(
                chat_id=dto.chat_tgid,
                user_id=dto.user_reply_tgid,
            )

    def is_different_sender(self, dto: ModerationActionDTO) -> bool:
        return dto.user_reply_tgid != dto.admin_tgid

    async def send_messages_to_admins(
        self,
        dto: ModerationActionDTO,
        text: str = None,
    ) -> None:
        # Получаем админов, которые подписаны на отслеживание чата
        admins = await self.user_service.get_admins_for_chat(
            chat_tg_id=dto.chat_tgid,
        )

        if not admins:
            return

        extended_text = (
            f"Администратор @{dto.admin_username} попытался выдать "
            f"предупреждение пользователю @{dto.user_reply_username} в чате {dto.chat_title},"
            "однако отсутсвует чат с историей удалённых сообщений.\n\n" + text
        )

        # Удаляем из списка админов текущего админа
        admins = [admin for admin in admins if admin.tg_id != dto.admin_tgid]

        # Отправляем сообщение админам в приватный чат
        for admin in admins:
            await self.bot_message_service.send_private_message(
                user_tgid=admin.tg_id,
                text=extended_text,
            )
