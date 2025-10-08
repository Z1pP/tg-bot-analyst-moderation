from datetime import datetime, timedelta
from typing import List, Optional

from constants.punishment import PunishmentText
from dto import ModerationActionDTO
from models import Punishment, User
from models.chat_session import ChatSession
from models.punishment_ladder import PunishmentLadder, PunishmentType
from repositories import PunishmentLadderRepository, PunishmentRepository
from repositories.user_chat_status_repository import UserChatStatusRepository
from services.time_service import TimeZoneService
from utils.formatter import format_seconds


class PunishmentService:
    """
    Сервис для управления наказаниями пользователей.

    Отвечает за:
    - Получение и подсчет наказаний из БД
    - Определение наказания по PunishmentLadder
    - Генерацию отчетов о наказаниях
    - Транзакционное сохранение наказания и статуса пользователя
    """

    def __init__(
        self,
        punishment_repository: PunishmentRepository,
        punishment_ladder_repository: PunishmentLadderRepository,
        user_chat_status_repository: UserChatStatusRepository,
    ):
        self.punishment_repository = punishment_repository
        self.punishment_ladder_repository = punishment_ladder_repository
        self.user_chat_status_repository = user_chat_status_repository

    def generate_admin_answer(
        self,
        archive_chats: List[ChatSession],
        punishment_type: PunishmentType,
    ) -> str:
        """
        Генерирует текст уведомления о наказании для отправки админу выдавшему наказание

        Args:
            archive_chats: список архивных чатов

        Returns:
            Форматированный текст
        """
        chats_title = [chat.title for chat in archive_chats]
        chats_title = "\n".join(chats_title)

        if punishment_type == PunishmentType.BAN:
            text = (
                "✅ Пользователь забанен!\n Данные отобразятся в "
                f"<b>{chats_title}</b>"
            )
            return text
        elif punishment_type == PunishmentType.MUTE:
            text = (
                "✅ Пользователь замучен!\n Данные отобразятся в "
                f"<b>{chats_title}</b>"
            )
            return text

        text = (
            "✅ Пользователь предупрежден!\n Данные отобразятся в "
            f"<b>{chats_title}</b>"
        )

        return text

    def generate_reason_for_user(
        self,
        duration_of_punishment: int,
        punished_username: str,
        punishment_type: PunishmentType = PunishmentType.WARNING,
    ) -> str:
        """
        Генерирует текст уведомления о наказании для отправки в чат.

        Args:
            duration_of_punishment: Длительность наказания в секундах
            punished_username: Username наказанного пользователя
            punishment_type: Тип наказания (WARNING/MUTE/BAN)

        Returns:
            Форматированный текст уведомления
        """
        punishment_text_template = PunishmentText[punishment_type.name].value

        if punishment_type == PunishmentType.MUTE:
            period = format_seconds(seconds=duration_of_punishment)
            return PunishmentText.MUTE.format(username=punished_username, period=period)

        return punishment_text_template.format(username=punished_username)

    async def get_punishment_count(self, user_id: int) -> int:
        """
        Получает количество наказаний пользователя.

        Args:
            user_id: ID пользователя в БД

        Returns:
            Количество наказаний
        """
        return await self.punishment_repository.get_punishment_count(user_id)

    async def get_punishment(
        self,
        warn_count: int,
        chat_id: str,
    ) -> Optional[PunishmentLadder]:
        """
        Определяет наказание по текущему количеству предупреждений.

        Если количество предупреждений >= максимального шага,
        возвращает максимальное наказание.

        Args:
            warn_count: Текущее количество предупреждений
            chat_id: Telegram ID чата

        Returns:
            Объект наказания из PunishmentLadder или None
        """
        max_punishment = await self.get_max_punishment(chat_id=chat_id)

        if max_punishment and warn_count >= max_punishment.step:
            return max_punishment

        return await self.punishment_ladder_repository.get_punishment_by_step(
            step=warn_count + 1,
            chat_id=chat_id,
        )

    async def get_max_punishment(self, chat_id: str) -> Optional[PunishmentLadder]:
        """
        Получает максимальное наказание для чата.

        Сначала ищет в настройках чата, затем в глобальных настройках.

        Args:
            chat_id: Telegram ID чата

        Returns:
            Максимальное наказание или None
        """
        ladder = await self.punishment_ladder_repository.get_ladder_by_chat_id(
            chat_id=chat_id,
        )
        if ladder:
            return ladder[-1]

        global_ladder = await self.punishment_ladder_repository.get_global_ladder()
        if global_ladder:
            return global_ladder[-1]

        return None

    def generate_ban_report(
        self,
        dto: ModerationActionDTO,
        date: datetime,
        message_deleted: bool = True,
    ) -> str:
        """
        Генерирует отчет о бане для архивного чата.

        Args:
            dto: Данные о действии модерации
            date: Дата и время наказания
            message_deleted: Было ли удалено сообщение

        Returns:
            Форматированный отчет
        """
        date_str = date.strftime("%d.%m.%Y")
        time_str = date.strftime("%H:%M")
        reason = dto.reason or "Не указана"
        status = "удалено" if message_deleted else "не удалено (старше 48ч)"

        return (
            f"❌️ Сообщение {status} {date_str} в {time_str}\n\n"
            f"• Юзер: @{dto.user_reply_username}\n"
            f"• ID: {dto.user_reply_tgid}\n"
            f"• Причина: {reason}\n"
            "• Время бана: бессрочно\n"
            f"• Выдал бан: @{dto.admin_username}\n"
            f"• Чат: {dto.chat_title}"
        )

    def generate_report(
        self,
        dto: ModerationActionDTO,
        punishment_ladder: PunishmentLadder,
        date: datetime,
        message_deleted: bool = True,
    ) -> str:
        """
        Генерирует отчет о наказании для архивного чата.

        Args:
            dto: Данные о действии модерации
            punishment: Примененное наказание
            date: Дата и время наказания
            message_deleted: Было ли удалено сообщение

        Returns:
            Форматированный отчет
        """
        date_str = date.strftime("%d.%m.%Y")
        time_str = date.strftime("%H:%M")
        reason = dto.reason or "Не указана"
        period = ""

        if punishment_ladder.punishment_type == PunishmentType.BAN:
            period = "бессрочно"
        elif punishment_ladder.punishment_type == PunishmentType.MUTE:
            period = format_seconds(seconds=punishment_ladder.duration_seconds)

        mute_line = f"• Время мута: {period}\n" if period else ""
        status = "удалено" if message_deleted else "не удалено (старше 48ч)"

        return (
            f"❌️ Сообщение {status} {date_str} в {time_str}\n\n"
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
        chat_id: int,
    ) -> Punishment:
        """
        Создает запись о наказании в БД.

        Args:
            user: Наказанный пользователь
            punishment: Примененное наказание
            admin_id: ID администратора
            chat_id: ID чата в БД

        Returns:
            Созданная запись наказания
        """
        new_punishment = Punishment(
            user_id=user.id,
            step=punishment.step,
            punishment_type=punishment.punishment_type,
            duration_seconds=punishment.duration_seconds,
            punished_by_id=admin_id,
            chat_id=chat_id,
        )
        return await self.punishment_repository.create_punishment(new_punishment)

    async def save_punishment_with_status(
        self,
        user: User,
        punishment: PunishmentLadder,
        admin_id: int,
        chat_id: int,
    ) -> None:
        """
        Транзакционно сохраняет наказание и обновляет статус пользователя.

        Создает запись наказания и обновляет статус пользователя в чате
        (is_muted/is_banned) в зависимости от типа наказания.

        Args:
            user: Наказанный пользователь
            punishment: Примененное наказание
            admin_id: ID администратора
            chat_id: ID чата в БД

        Raises:
            Exception: При ошибках сохранения в БД
        """
        await self.create_punishment(
            user=user,
            punishment=punishment,
            admin_id=admin_id,
            chat_id=chat_id,
        )

        current_date = TimeZoneService.now()

        if punishment.punishment_type == PunishmentType.MUTE:
            muted_until = None
            if punishment.duration_seconds is not None:
                muted_until = current_date + timedelta(
                    seconds=punishment.duration_seconds
                )
            await self.user_chat_status_repository.update_status(
                user_id=user.id,
                chat_id=chat_id,
                is_muted=True,
                muted_until=muted_until,
            )
        elif punishment.punishment_type == PunishmentType.BAN:
            await self.user_chat_status_repository.update_status(
                user_id=user.id,
                chat_id=chat_id,
                is_banned=True,
                banned_until=None,
                is_muted=False,
                muted_until=None,
            )
