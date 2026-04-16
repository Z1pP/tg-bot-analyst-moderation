import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import (
    Chat,
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

    def __init__(self, bot: Bot) -> None:
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
        self, user_id: int, chat_tgid: ChatIdUnion
    ) -> ChatMemberStatus:
        """Получает информацию о статусе пользователя в чате."""
        status = ChatMemberStatus()

        try:
            member = await self.bot.get_chat_member(chat_id=chat_tgid, user_id=user_id)
        except TelegramAPIError as e:
            logger.warning(
                "Не удалось получить статус участника %s в чате %s: %s",
                user_id,
                chat_tgid,
                e,
            )
            return status

        if isinstance(member, ChatMemberBanned):
            status.is_banned = True
            if member.until_date:
                status.banned_until = TimeZoneService.convert_to_local_time(
                    member.until_date
                )
        elif isinstance(member, ChatMemberRestricted):
            status.is_muted = not member.can_send_messages
            if member.until_date:
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

    async def _has_bot_permission(self, chat_tgid: ChatIdUnion, attr_name: str) -> bool:
        """
        Проверяет наличие у бота права (атрибута администратора).
        Владелец чата считается имеющим все права.
        """
        member = await self.get_bot_member(chat_tgid=chat_tgid)
        if not member:
            return False
        if isinstance(member, ChatMemberOwner):
            return True
        if isinstance(member, ChatMemberAdministrator):
            return getattr(member, attr_name, False)
        return False

    async def get_chat_from_telegram(self, chat_tgid: ChatIdUnion) -> Optional[Chat]:
        """Возвращает актуальные данные чата из Telegram API."""
        try:
            return await self.bot.get_chat(chat_id=chat_tgid)
        except TelegramAPIError as e:
            logger.warning("Не удалось получить чат %s из Telegram: %s", chat_tgid, e)
            return None

    async def is_channel(self, chat_tgid: ChatIdUnion) -> bool:
        """Возвращает True, если чат — канал."""
        chat = await self.get_chat_from_telegram(chat_tgid)
        return chat.type == "channel" if chat else False

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
        return await self._has_bot_permission(chat_tgid, "can_restrict_members")

    async def can_delete_messages(self, chat_tgid: ChatIdUnion) -> bool:
        """Проверяет право бота на удаление сообщений."""
        return await self._has_bot_permission(chat_tgid, "can_delete_messages")

    async def can_post_messages(self, chat_tgid: ChatIdUnion) -> bool:
        """Проверяет право бота на отправку сообщений (корректно для групп и каналов)."""
        is_channel = await self.is_channel(chat_tgid)
        if is_channel:
            return await self._has_bot_permission(chat_tgid, "can_post_messages")
        member = await self.get_bot_member(chat_tgid=chat_tgid)
        if not member or member.status in ("left", "kicked"):
            return False
        if isinstance(member, ChatMemberRestricted):
            return member.can_send_messages
        return True

    async def can_invite_users(self, chat_tgid: ChatIdUnion) -> bool:
        """Проверяет право бота на создание приглашений."""
        return await self._has_bot_permission(chat_tgid, "can_invite_users")

    async def is_administrator(self, user_id: int, chat_tgid: ChatIdUnion) -> bool:
        """Проверяет, является ли пользователь администратором."""
        try:
            member = await self.bot.get_chat_member(chat_id=chat_tgid, user_id=user_id)
            return isinstance(member, (ChatMemberOwner, ChatMemberAdministrator))
        except TelegramAPIError as e:
            logger.error(
                "Ошибка проверки админ-прав для %s в чате %s: %s",
                user_id,
                chat_tgid,
                e,
            )
            return False

    async def is_member_banned(self, user_id: int, chat_tgid: ChatIdUnion) -> bool:
        """Проверяет бан пользователя."""
        try:
            member = await self.bot.get_chat_member(chat_id=chat_tgid, user_id=user_id)
            return isinstance(member, ChatMemberBanned)
        except TelegramAPIError as e:
            logger.error(
                "Ошибка проверки бана для %s в чате %s: %s",
                user_id,
                chat_tgid,
                e,
            )
            return False

    async def is_member_muted(self, user_id: int, chat_tgid: ChatIdUnion) -> bool:
        """Проверяет мут пользователя."""
        try:
            member = await self.bot.get_chat_member(chat_id=chat_tgid, user_id=user_id)
            if isinstance(member, ChatMemberRestricted):
                return not member.can_send_messages
            return False
        except TelegramAPIError as e:
            logger.error(
                "Ошибка проверки мута для %s в чате %s: %s",
                user_id,
                chat_tgid,
                e,
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

        is_channel = await self.is_channel(chat_tgid)

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

        elif not is_admin:
            logger.info("Бот не является администратором в чате %s", chat_tgid)
            missing_permissions = [
                name
                for attr, name in permission_names.items()
                if not (attr == "can_post_messages" and not is_channel)
            ]

        return BotPermissionsCheck(
            is_admin=is_admin,
            missing_permissions=missing_permissions,
            has_all_permissions=len(missing_permissions) == 0,
            is_member=is_member,
            status=member.status,
        )
