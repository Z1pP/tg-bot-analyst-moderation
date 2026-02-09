import logging
from datetime import datetime, timedelta
from typing import List, Optional

from constants import Dialog
from constants.punishment import PunishmentText
from dto import ModerationActionDTO
from models import Punishment, User
from models.punishment_ladder import PunishmentLadder, PunishmentType
from repositories import PunishmentLadderRepository, PunishmentRepository
from repositories.user_chat_status_repository import UserChatStatusRepository
from services.time_service import TimeZoneService
from utils.formatter import format_duration

logger = logging.getLogger(__name__)


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
            period = format_duration(seconds=duration_of_punishment)
            return PunishmentText.MUTE.format(username=punished_username, period=period)

        return punishment_text_template.format(username=punished_username)

    async def get_punishment_count(
        self, user_id: int, chat_id: Optional[int] = None
    ) -> int:
        """
        Получает количество наказаний пользователя.

        Args:
            user_id: ID пользователя в БД
            chat_id: ID чата в БД (опционально)

        Returns:
            Количество наказаний
        """
        return await self.punishment_repository.count_punishments(
            user_id=user_id, chat_id=chat_id
        )

    async def get_punishment(
        self,
        warn_count: int,
        chat_id: str,
    ) -> PunishmentLadder:
        """
        Определяет наказание по текущему количеству предупреждений.

        Если количество предупреждений >= максимального шага,
        возвращает максимальное наказание.
        Если лестница пуста, возвращает дефолтное предупреждение.

        Args:
            warn_count: Текущее количество предупреждений
            chat_id: Telegram ID чата

        Returns:
            Объект наказания из PunishmentLadder
        """
        max_punishment = await self.get_max_punishment(chat_id=chat_id)

        if max_punishment:
            if warn_count >= max_punishment.step:
                return max_punishment

            punishment = await self.punishment_ladder_repository.get_punishment_by_step(
                step=warn_count + 1,
                chat_id=chat_id,
            )
            if punishment:
                return punishment

        # Дефолтный фолбек, если лестница не настроена
        logger.warning(
            "Лестница наказаний не настроена для чата %s. Используется дефолтное предупреждение.",
            chat_id,
        )
        return PunishmentLadder(
            step=warn_count + 1,
            punishment_type=PunishmentType.WARNING,
            duration_seconds=0,
            chat_id=None,
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

    @staticmethod
    def _format_punishment_period(
        punishment_type: PunishmentType, duration_seconds: Optional[int]
    ) -> str:
        """
        Форматирует длительность наказания в понятную строку.

        Args:
            punishment_type: Тип наказания
            duration_seconds: Длительность в секундах

        Returns:
            Строка с описанием длительности
        """
        if punishment_type == PunishmentType.BAN:
            return Dialog.ModerationReport.INFINITE_PERIOD
        if punishment_type == PunishmentType.MUTE and duration_seconds:
            return format_duration(seconds=duration_seconds)
        return ""

    @staticmethod
    def _get_message_deletion_status(message_deleted: bool) -> str:
        """
        Возвращает текстовый статус удаления сообщения.

        Args:
            message_deleted: Флаг удаления

        Returns:
            Текстовое описание статуса
        """
        return "удалено" if message_deleted else "не удалено (старше 48ч)"

    @classmethod
    def _build_report_header(cls, date: datetime, message_deleted: bool) -> str:
        """
        Генерирует заголовок отчета.

        Args:
            date: Дата события
            message_deleted: Флаг удаления сообщения

        Returns:
            Строка заголовка
        """
        return Dialog.ModerationReport.REPORT_HEADER

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
        header = self._build_report_header(date, message_deleted)
        reason = dto.reason or Dialog.ModerationReport.NO_REASON
        period = self._format_punishment_period(PunishmentType.BAN, None)
        date_str = date.strftime("%d.%m.%Y %H:%M")

        return Dialog.ModerationReport.REPORT_BODY.format(
            header=header,
            admin_username=dto.admin_username,
            date_str=date_str,
            violator_username=dto.violator_username,
            violator_tgid=dto.violator_tgid,
            reason=reason,
            chat_title=dto.chat_title,
            punishment_name=Dialog.ModerationReport.PUNISHMENT_NAMES["BAN"],
            period=period,
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
            punishment_ladder: Примененное наказание
            date: Дата и время наказания
            message_deleted: Было ли удалено сообщение

        Returns:
            Форматированный отчет
        """
        header = self._build_report_header(date, message_deleted)
        reason = dto.reason or Dialog.ModerationReport.NO_REASON
        period = self._format_punishment_period(
            punishment_ladder.punishment_type, punishment_ladder.duration_seconds
        )
        date_str = date.strftime("%d.%m.%Y %H:%M")

        punishment_name = Dialog.ModerationReport.PUNISHMENT_NAMES.get(
            punishment_ladder.punishment_type.name,
            punishment_ladder.punishment_type.value,
        )

        return Dialog.ModerationReport.REPORT_BODY.format(
            header=header,
            admin_username=dto.admin_username,
            date_str=date_str,
            violator_username=dto.violator_username,
            violator_tgid=dto.violator_tgid,
            reason=reason,
            chat_title=dto.chat_title,
            punishment_name=punishment_name,
            period=period or Dialog.ModerationReport.NO_PERIOD,
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

    async def delete_user_punishments(self, user_id: int, chat_id: int) -> int:
        """
        Удаляет все наказания пользователя в конкретном чате.

        Args:
            user_id: ID пользователя в БД
            chat_id: ID чата в БД

        Returns:
            Количество удаленных записей
        """
        return await self.punishment_repository.delete_user_punishments(
            user_id, chat_id
        )

    def format_ladder_text(self, ladder: List[PunishmentLadder]) -> str:
        """
        Форматирует лестницу наказаний в текст для вывода в интерфейс.

        Args:
            ladder: Список ступеней лестницы наказаний

        Returns:
            Форматированный текст (HTML)
        """
        if not ladder:
            return Dialog.Punishment.LADDER_EMPTY

        digit_map = {
            "0": "0️⃣",
            "1": "1️⃣",
            "2": "2️⃣",
            "3": "3️⃣",
            "4": "4️⃣",
            "5": "5️⃣",
            "6": "6️⃣",
            "7": "7️⃣",
            "8": "8️⃣",
            "9": "9️⃣",
        }

        def step_to_emoji(step: int) -> str:
            return "".join(digit_map.get(ch, ch) for ch in str(step))

        ladder_lines = []
        for p in ladder:
            step_emoji = step_to_emoji(p.step)
            if p.punishment_type == PunishmentType.WARNING:
                label = "Предупреждение"
            elif p.punishment_type == PunishmentType.MUTE:
                if p.duration_seconds:
                    label = f"Ограничение - {format_duration(p.duration_seconds)}"
                else:
                    label = "Ограничение"
            elif p.punishment_type == PunishmentType.BAN:
                label = "Блокировка"
            else:
                label = p.punishment_type.value

            ladder_lines.append(f"{step_emoji} {label}")

        return "\n".join(ladder_lines)
