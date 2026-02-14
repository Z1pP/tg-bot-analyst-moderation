import logging
from dataclasses import dataclass
from typing import Optional

from constants.enums import AdminActionType
from models import AdminChatAccess, ChatSession, User
from repositories import ChatTrackingRepository
from services import (
    AdminActionLogService,
    BotPermissionService,
    ChatService,
    UserService,
)
from services.permissions.bot_permission import BotPermissionsCheck
from services.time_service import TimeZoneService

logger = logging.getLogger(__name__)


@dataclass
class AddChatToTrackResult:
    """Результат выполнения UseCase добавления чата в отслеживание."""

    admin: Optional[User] = None
    chat: Optional[ChatSession] = None
    access: Optional[AdminChatAccess] = None
    is_already_tracked: bool = False
    permissions_check: Optional[BotPermissionsCheck] = None
    success: bool = False
    error_message: Optional[str] = None


class AddChatToTrackUseCase:
    """
    UseCase для добавления чата в список для отслеживания.
    Теперь сам получает админа, чат и проверяет права бота.
    """

    def __init__(
        self,
        chat_tracking_repository: ChatTrackingRepository,
        admin_action_log_service: AdminActionLogService,
        user_service: UserService,
        chat_service: ChatService,
        bot_permission_service: BotPermissionService,
    ):
        self._chat_tracking_repository = chat_tracking_repository
        self._admin_action_log_service = admin_action_log_service
        self._user_service = user_service
        self._chat_service = chat_service
        self._bot_permission_service = bot_permission_service

    async def execute(
        self,
        admin_tg_id: str,
        chat_tg_id: str,
        chat_title: str,
        admin_username: Optional[str] = None,
    ) -> AddChatToTrackResult:
        """
        Выполняет процесс добавления чата в отслеживание.

        Args:
            admin_tg_id: Telegram ID администратора
            chat_tg_id: Telegram ID чата
            chat_title: Название чата
            admin_username: Username администратора

        Returns:
            AddChatToTrackResult: Результат выполнения
        """
        result = AddChatToTrackResult()

        try:
            # 1. Получаем администратора
            admin = await self._user_service.get_user(
                tg_id=admin_tg_id, username=admin_username
            )
            if not admin:
                logger.warning("Администратор не найден в БД: %s", admin_tg_id)
                result.error_message = "Администратор не найден"
                return result
            result.admin = admin

            # 2. Получаем или создаем чат
            chat = await self._chat_service.get_or_create(
                chat_tgid=chat_tg_id, title=chat_title or "Без названия"
            )
            if not chat:
                logger.error("Не удалось получить или создать чат: %s", chat_tg_id)
                result.error_message = "Не удалось получить чат"
                return result
            result.chat = chat

            # 3. Проверяем права бота в чате
            permissions_check = (
                await self._bot_permission_service.check_archive_permissions(
                    chat_tgid=chat_tg_id
                )
            )
            result.permissions_check = permissions_check

            if not permissions_check.has_all_permissions:
                logger.warning(
                    "Недостаточно прав бота в чате '%s' (%s): %s",
                    chat.title,
                    chat.chat_id,
                    permissions_check.missing_permissions,
                )
                return result

            # 4. Проверяем, отслеживается ли уже чат
            existing_access = await self._chat_tracking_repository.get_access(
                admin_id=admin.id,
                chat_id=chat.id,
            )
            if existing_access:
                result.access = existing_access
                result.is_already_tracked = True
                result.success = True
                return result

            # 5. Добавляем чат в список отслеживаемых
            chat_access = await self._chat_tracking_repository.add_chat_to_tracking(
                admin_id=admin.id,
                chat_id=chat.id,
                is_source=False,
                is_target=False,
            )
            if not chat_access:
                result.error_message = "Не удалось добавить чат в отслеживание"
                return result

            result.access = chat_access
            result.success = True

            # 6. Логируем действие администратора
            admin_who = f"@{admin.username}" if admin.username else f"ID:{admin.tg_id}"
            when_str = TimeZoneService.now().strftime("%d.%m.%Y %H:%M")
            chat_name = chat.title or f"ID:{chat.chat_id}"
            details = (
                "➕ Добавление чата\n"
                f"Кто: {admin_who}\n"
                f"Когда: {when_str}\n"
                f"Чат: {chat_name}"
            )
            await self._admin_action_log_service.log_action(
                admin_tg_id=admin.tg_id,
                action_type=AdminActionType.ADD_CHAT,
                details=details,
            )

            logger.info(
                "Чат '%s' успешно добавлен в отслеживание админом %s",
                chat.title,
                admin.username,
            )
            return result

        except Exception as e:
            logger.error(
                "Ошибка при выполнении UseCase AddChatToTrackUseCase: %s",
                e,
                exc_info=True,
            )
            result.error_message = str(e)
            return result
