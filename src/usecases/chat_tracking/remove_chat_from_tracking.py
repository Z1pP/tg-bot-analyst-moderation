import logging
from dataclasses import dataclass
from typing import Optional

from constants.enums import AdminActionType
from models import ChatSession, User
from repositories import ChatTrackingRepository
from services import (
    AdminActionLogService,
    BotPermissionService,
    ChatService,
    UserService,
)
from services.permissions.bot_permission import BotPermissionsCheck

logger = logging.getLogger(__name__)


@dataclass
class RemoveChatFromTrackingResult:
    """Результат выполнения UseCase удаления чата из отслеживания."""

    admin: Optional[User] = None
    chat: Optional[ChatSession] = None
    success: bool = False
    is_chat_not_tracked: bool = False
    permissions_check: Optional[BotPermissionsCheck] = None
    error_message: Optional[str] = None


class RemoveChatFromTrackingUseCase:
    """
    UseCase для удаления чата из списка отслеживания.
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
    ) -> RemoveChatFromTrackingResult:
        """
        Выполняет процесс удаления чата из отслеживания.

        Args:
            admin_tg_id: Telegram ID администратора
            chat_tg_id: Telegram ID чата
            chat_title: Название чата
            admin_username: Username администратора

        Returns:
            RemoveChatFromTrackingResult: Результат выполнения
        """
        result = RemoveChatFromTrackingResult()

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

            # 2. Получаем чат
            chat = await self._chat_service.get_chat(
                chat_tgid=chat_tg_id, title=chat_title
            )
            if not chat:
                logger.warning("Чат не найден в БД: %s", chat_tg_id)
                result.error_message = "Чат не найден"
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

            # 4. Проверяем, отслеживается ли чат
            existing_access = await self._chat_tracking_repository.get_access(
                admin_id=admin.id,
                chat_id=chat.id,
            )
            if not existing_access:
                logger.info(
                    "Чат '%s' (%s) не отслеживается админом %s",
                    chat.title,
                    chat.chat_id,
                    admin.username,
                )
                result.is_chat_not_tracked = True
                result.success = False
                return result

            # 5. Удаляем чат из отслеживания
            success = await self._chat_tracking_repository.remove_chat_from_tracking(
                admin_id=admin.id,
                chat_id=chat.id,
            )

            if not success:
                logger.error(
                    "Не удалось удалить чат '%s' (%s) из отслеживания для админа %s",
                    chat.title,
                    chat.chat_id,
                    admin.username,
                )
                result.error_message = "Не удалось удалить чат из отслеживания"
                return result

            result.success = True

            # 6. Логируем действие администратора
            await self._admin_action_log_service.log_action(
                admin_tg_id=admin.tg_id,
                action_type=AdminActionType.REMOVE_CHAT,
                details=f"Чат: {chat.title} ({chat.chat_id})",
            )

            logger.info(
                "Чат '%s' успешно удален из отслеживания админом %s",
                chat.title,
                admin.username,
            )
            return result

        except Exception as e:
            logger.error(
                "Ошибка при выполнении UseCase RemoveChatFromTrackingUseCase: %s",
                e,
                exc_info=True,
            )
            result.error_message = str(e)
            return result
