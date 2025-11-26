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


class BotPermissionService:
    """
    Сервис для проверки прав бота и пользователей в чатах.

    Отвечает за:
    - Проверку прав бота на модерацию
    - Проверку статуса администратора пользователя
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    async def get_chat_member_status(
        self, user_tgid: int, chat_tgid: ChatIdUnion
    ) -> ChatMemberStatus:
        """Получает информацию о статусе пользователя в чате."""
        status = ChatMemberStatus()

        try:
            member = await self.bot.get_chat_member(
                chat_id=chat_tgid, user_id=user_tgid
            )
        except TelegramAPIError:
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
        else:
            status.is_banned = False
            status.is_muted = False

        return status

    async def get_bot_member(self, chat_tgid: ChatIdUnion) -> ResultChatMemberUnion:
        """
        Получает информацию о боте как участнике чата.

        Args:
            chat_tgid: Telegram ID чата

        Returns:
            Информация о члене чата (боте)
        """
        return await self.bot.get_chat_member(chat_id=chat_tgid, user_id=self.bot.id)

    async def can_moderate(self, chat_tgid: ChatIdUnion) -> bool:
        """
        Проверяет, может ли бот модерировать чат (блокировать и мутить пользователей).

        Бот может модерировать, если он:
        - Является администратором или владельцем
        - Имеет право can_restrict_members

        Args:
            chat_tgid: Telegram ID чата

        Returns:
            True если бот может модерировать (блокировать и мутить)
        """
        member = await self.get_bot_member(chat_tgid=chat_tgid)

        if isinstance(member, ChatMemberOwner):
            return True
        if isinstance(member, ChatMemberAdministrator):
            return (
                member.can_restrict_members
                if hasattr(member, "can_restrict_members")
                else False
            )
        return False

    async def can_ban_users(self, chat_tgid: ChatIdUnion) -> bool:
        """
        Проверяет, может ли бот блокировать пользователей в чате.

        Args:
            chat_tgid: Telegram ID чата

        Returns:
            True если бот может блокировать пользователей
        """
        return await self.can_moderate(chat_tgid=chat_tgid)

    async def can_mute_users(self, chat_tgid: ChatIdUnion) -> bool:
        """
        Проверяет, может ли бот мутить пользователей в чате.

        Args:
            chat_tgid: Telegram ID чата

        Returns:
            True если бот может мутить пользователей
        """
        return await self.can_moderate(chat_tgid=chat_tgid)

    async def can_delete_messages(self, chat_tgid: ChatIdUnion) -> bool:
        """
        Проверяет, может ли бот удалять сообщения в чате.

        Args:
            chat_tgid: Telegram ID чата

        Returns:
            True если бот может удалять сообщения
        """
        member = await self.get_bot_member(chat_tgid=chat_tgid)

        if isinstance(member, ChatMemberOwner):
            return True
        if isinstance(member, ChatMemberAdministrator):
            return (
                member.can_delete_messages
                if hasattr(member, "can_delete_messages")
                else False
            )
        return False

    async def can_post_messages(self, chat_tgid: ChatIdUnion) -> bool:
        """
        Проверяет, может ли бот отправлять сообщения в чате.

        Args:
            chat_tgid: Telegram ID чата

        Returns:
            True если бот может отправлять сообщения
        """
        member = await self.get_bot_member(chat_tgid=chat_tgid)

        if isinstance(member, ChatMemberOwner):
            return True
        if isinstance(member, ChatMemberAdministrator):
            return (
                member.can_post_messages
                if hasattr(member, "can_post_messages")
                else True
            )
        return False

    async def is_administrator(
        self, tg_id: ChatIdUnion, chat_tg_id: ChatIdUnion
    ) -> bool:
        """
        Проверяет, является ли пользователь администратором чата.

        Args:
            tg_id: Telegram ID пользователя
            chat_tg_id: Telegram ID чата

        Returns:
            True если пользователь - администратор или владелец
        """
        member = await self.bot.get_chat_member(chat_id=chat_tg_id, user_id=tg_id)
        return isinstance(member, (ChatMemberOwner, ChatMemberAdministrator))

    async def is_member_banned(
        self, tg_id: ChatIdUnion, chat_tg_id: ChatIdUnion
    ) -> bool:
        """
        Проверяет, заблокирован ли пользователь в чате.

        Args:
            tg_id: Telegram ID пользователя
            chat_tg_id: Telegram ID чата

        Returns:
            True если пользователь заблокирован
        """
        member = await self.bot.get_chat_member(chat_id=chat_tg_id, user_id=int(tg_id))
        return isinstance(member, ChatMemberBanned)

    async def is_member_muted(
        self, tg_id: ChatIdUnion, chat_tg_id: ChatIdUnion
    ) -> bool:
        """
        Проверяет, замучен ли пользователь в чате.

        Args:
            tg_id: Telegram ID пользователя
            chat_tg_id: Telegram ID чата

        Returns:
            True если пользователь ограничен в правах (мут)
        """
        member = await self.bot.get_chat_member(chat_id=chat_tg_id, user_id=int(tg_id))
        return isinstance(member, ChatMemberRestricted) and not member.can_send_messages

    async def can_invite_users(self, chat_tgid: ChatIdUnion) -> bool:
        """
        Проверяет, может ли бот создавать пригласительные ссылки в чате.

        Args:
            chat_tgid: Telegram ID чата

        Returns:
            True если бот может создавать invite ссылки
        """
        member = await self.get_bot_member(chat_tgid=chat_tgid)

        if isinstance(member, ChatMemberOwner):
            return True
        if isinstance(member, ChatMemberAdministrator):
            return (
                member.can_invite_users
                if hasattr(member, "can_invite_users")
                else False
            )
        return False

    async def check_archive_permissions(
        self, chat_tgid: ChatIdUnion
    ) -> BotPermissionsCheck:
        """
        Проверяет все необходимые права бота для работы с архивным чатом.

        Проверяемые права:
        - can_restrict_members - для блокировки и мута пользователей
        - can_invite_users - для получения invite ссылки
        - can_delete_messages - для удаления сообщений
        - can_post_messages - для отправки отчетов в архив (только для каналов)

        Args:
            chat_tgid: Telegram ID чата

        Returns:
            BotPermissionsCheck с информацией о недостающих правах
        """
        member = await self.get_bot_member(chat_tgid=chat_tgid)

        # Определяем тип чата для корректной проверки can_post_messages
        try:
            chat = await self.bot.get_chat(chat_id=chat_tgid)
            is_channel = chat.type == "channel"
        except TelegramAPIError:
            # Если не удалось получить информацию о чате, считаем что это группа
            is_channel = False

        # Маппинг прав на читаемые названия
        permission_names = {
            "can_restrict_members": "Блокировка и мут пользователей",
            "can_invite_users": "Создание пригласительных ссылок",
            "can_delete_messages": "Удаление сообщений",
            "can_post_messages": "Отправка сообщений",
        }

        is_admin = isinstance(member, (ChatMemberOwner, ChatMemberAdministrator))
        missing_permissions = []

        # Для владельца все права доступны
        if isinstance(member, ChatMemberOwner):
            return BotPermissionsCheck(
                is_admin=True,
                missing_permissions=[],
                has_all_permissions=True,
            )

        # Для администратора проверяем каждое право
        if isinstance(member, ChatMemberAdministrator):
            # Проверка can_restrict_members (блокировка и мут)
            if not (
                hasattr(member, "can_restrict_members") and member.can_restrict_members
            ):
                missing_permissions.append(permission_names["can_restrict_members"])

            # Проверка can_invite_users
            if not (hasattr(member, "can_invite_users") and member.can_invite_users):
                missing_permissions.append(permission_names["can_invite_users"])

            # Проверка can_delete_messages
            if not (
                hasattr(member, "can_delete_messages") and member.can_delete_messages
            ):
                missing_permissions.append(permission_names["can_delete_messages"])

            # Проверка can_post_messages
            # Для каналов проверяем can_post_messages (право публиковать от имени канала)
            # Для групп (supergroup) это право не применимо - бот-админ может отправлять сообщения
            if is_channel:
                if not (
                    hasattr(member, "can_post_messages") and member.can_post_messages
                ):
                    missing_permissions.append(permission_names["can_post_messages"])
            # Для групп не проверяем can_post_messages - бот-админ может отправлять сообщения

        # Если бот не администратор, все права отсутствуют
        if not is_admin:
            missing_permissions = list(permission_names.values())

        return BotPermissionsCheck(
            is_admin=is_admin,
            missing_permissions=missing_permissions,
            has_all_permissions=len(missing_permissions) == 0,
        )

    async def check_all_required_permissions(
        self, chat_tgid: ChatIdUnion
    ) -> BotPermissionsCheck:
        """
        Проверяет все обязательные права бота для полноценной работы.

        Проверяемые права:
        - can_restrict_members - для блокировки и мута пользователей
        - can_invite_users - для получения пригласительных ссылок
        - can_delete_messages - для удаления сообщений
        - can_post_messages - для отправки сообщений в чат

        Args:
            chat_tgid: Telegram ID чата

        Returns:
            BotPermissionsCheck с информацией о недостающих правах
        """
        return await self.check_archive_permissions(chat_tgid=chat_tgid)
