import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import (
    ChatIdUnion,
    ChatMemberAdministrator,
    ChatMemberBanned,
    ChatMemberOwner,
    ChatMemberRestricted,
    ResultChatMemberUnion,
)

from services.time_service import TimeZoneService

logger = logging.getLogger(__name__)


@dataclass
class ChatMemberStatus:
    is_banned: bool = False
    is_muted: bool = False
    banned_until: Optional[datetime] = None
    muted_until: Optional[datetime] = None


@dataclass
class BotPermissionsCheck:
    """Результат проверки прав бота для работы с архивом."""

    is_admin: bool
    missing_permissions: List[str]
    has_all_permissions: bool
    is_member: bool = True
    status: str = "member"


class BotPermissionService:
    """
    Сервис для проверки прав бота и пользователей в чатах.
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    async def get_total_members(
        self,
        chat_tgid: ChatIdUnion,
    ) -> int:
        """Получает общее количество участников чата."""
        try:
            total = await self.bot.get_chat_member_count(chat_id=chat_tgid)
            return total
        except TelegramAPIError as e:
            logger.error(
                "Ошибка при получении количества участников чата %s: %s",
                chat_tgid,
                e,
                exc_info=True,
            )
            return 0

    async def get_chat_member_status(
        self, user_tgid: int, chat_tgid: ChatIdUnion
    ) -> ChatMemberStatus:
        """Получает информацию о статусе пользователя в чате."""
        status = ChatMemberStatus()

        try:
            member = await self.bot.get_chat_member(
                chat_id=chat_tgid, user_id=user_tgid
            )
        except TelegramAPIError as e:
            logger.warning(
                "Не удалось получить статус участника %s в чате %s: %s",
                user_tgid,
                chat_tgid,
                e,
            )
            return status

        if isinstance(member, ChatMemberBanned):
            status.is_banned = True
            status.banned_until = TimeZoneService.convert_to_local_time(
                member.until_date
            )
        elif isinstance(member, ChatMemberRestricted):
            status.is_muted = not member.can_send_messages
            status.muted_until = TimeZoneService.convert_to_local_time(
                member.until_date
            )
        return status

    async def get_bot_member(
        self, chat_tgid: ChatIdUnion
    ) -> Optional[ResultChatMemberUnion]:
        """Получает информацию о боте как участнике чата."""
        try:
            return await self.bot.get_chat_member(
                chat_id=chat_tgid, user_id=self.bot.id
            )
        except TelegramAPIError as e:
            logger.error(
                "Ошибка при получении статуса бота в чате %s: %s", chat_tgid, e
            )
            return None

    async def is_bot_in_chat(self, chat_tgid: ChatIdUnion) -> bool:
        """Проверяет, состоит ли бот в чате."""
        member = await self.get_bot_member(chat_tgid=chat_tgid)
        if not member:
            return False

        if member.status in ("left", "kicked"):
            return False

        return True

    async def can_moderate(self, chat_tgid: ChatIdUnion) -> bool:
        """Проверяет право бота на модерацию."""
        member = await self.get_bot_member(chat_tgid=chat_tgid)
        if not member:
            return False

        if isinstance(member, ChatMemberOwner):
            return True
        if isinstance(member, ChatMemberAdministrator):
            return getattr(member, "can_restrict_members", False)
        return False

    async def can_delete_messages(self, chat_tgid: ChatIdUnion) -> bool:
        """Проверяет право бота на удаление сообщений."""
        member = await self.get_bot_member(chat_tgid=chat_tgid)
        if not member:
            return False

        if isinstance(member, ChatMemberOwner):
            return True
        if isinstance(member, ChatMemberAdministrator):
            return getattr(member, "can_delete_messages", False)
        return False

    async def can_post_messages(self, chat_tgid: ChatIdUnion) -> bool:
        """Проверяет право бота на отправку сообщений."""
        member = await self.get_bot_member(chat_tgid=chat_tgid)
        if not member:
            return False

        if isinstance(member, (ChatMemberOwner, ChatMemberAdministrator)):
            return True

        return False

    async def can_invite_users(self, chat_tgid: ChatIdUnion) -> bool:
        """Проверяет право бота на создание приглашений."""
        member = await self.get_bot_member(chat_tgid=chat_tgid)
        if not member:
            return False

        if isinstance(member, ChatMemberOwner):
            return True
        if isinstance(member, ChatMemberAdministrator):
            return getattr(member, "can_invite_users", False)
        return False

    async def is_administrator(
        self, tg_id: ChatIdUnion, chat_tg_id: ChatIdUnion
    ) -> bool:
        """Проверяет, является ли пользователь администратором."""
        try:
            member = await self.bot.get_chat_member(
                chat_id=chat_tg_id, user_id=int(tg_id)
            )
            return isinstance(member, (ChatMemberOwner, ChatMemberAdministrator))
        except TelegramAPIError as e:
            logger.error(
                "Ошибка проверки админ-прав для %s в чате %s: %s", tg_id, chat_tg_id, e
            )
            return False

    async def is_member_banned(
        self, tg_id: ChatIdUnion, chat_tg_id: ChatIdUnion
    ) -> bool:
        """Проверяет бан пользователя."""
        try:
            member = await self.bot.get_chat_member(
                chat_id=chat_tg_id, user_id=int(tg_id)
            )
            return isinstance(member, ChatMemberBanned)
        except TelegramAPIError as e:
            logger.error(
                "Ошибка проверки бана для %s в чате %s: %s", tg_id, chat_tg_id, e
            )
            return False

    async def is_member_muted(
        self, tg_id: ChatIdUnion, chat_tg_id: ChatIdUnion
    ) -> bool:
        """Проверяет мут пользователя."""
        try:
            member = await self.bot.get_chat_member(
                chat_id=chat_tg_id, user_id=int(tg_id)
            )
            if isinstance(member, ChatMemberRestricted):
                return not member.can_send_messages
            return False
        except TelegramAPIError as e:
            logger.error(
                "Ошибка проверки мута для %s в чате %s: %s", tg_id, chat_tg_id, e
            )
            return False

    async def check_archive_permissions(
        self, chat_tgid: ChatIdUnion
    ) -> BotPermissionsCheck:
        """Проверяет все необходимые права бота."""
        member = await self.get_bot_member(chat_tgid=chat_tgid)

        if not member:
            return BotPermissionsCheck(
                is_admin=False,
                missing_permissions=["Не удалось получить статус бота"],
                has_all_permissions=False,
                is_member=False,
                status="not_member",
            )

        try:
            chat = await self.bot.get_chat(chat_id=chat_tgid)
            is_channel = chat.type == "channel"
        except TelegramAPIError as e:
            logger.warning(
                "Не удалось получить тип чата %s, считаем группой: %s", chat_tgid, e
            )
            is_channel = False

        permission_names = {
            "can_restrict_members": "Блокировка и мут пользователей",
            "can_invite_users": "Создание пригласительных ссылок",
            "can_delete_messages": "Удаление сообщений",
            "can_post_messages": "Отправка сообщений",
        }

        is_admin = isinstance(member, (ChatMemberOwner, ChatMemberAdministrator))
        is_member = member.status not in ("left", "kicked")
        missing_permissions = []

        if isinstance(member, ChatMemberOwner):
            return BotPermissionsCheck(
                is_admin=True,
                missing_permissions=[],
                has_all_permissions=True,
                is_member=is_member,
                status=member.status,
            )

        if isinstance(member, ChatMemberAdministrator):
            # Проверяем атрибуты динамически, так как они могут отсутствовать в разных версиях API/типах чата
            for attr, name in permission_names.items():
                if attr == "can_post_messages" and not is_channel:
                    continue
                if not getattr(member, attr, False):
                    missing_permissions.append(name)

        if not is_admin:
            missing_permissions = list(permission_names.values())
            logger.info("Бот не является администратором в чате %s", chat_tgid)

        return BotPermissionsCheck(
            is_admin=is_admin,
            missing_permissions=missing_permissions,
            has_all_permissions=len(missing_permissions) == 0,
            is_member=is_member,
            status=member.status,
        )
