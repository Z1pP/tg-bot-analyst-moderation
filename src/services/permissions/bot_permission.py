from aiogram import Bot
from aiogram.types import (
    ChatIdUnion,
    ChatMemberAdministrator,
    ChatMemberOwner,
    ResultChatMemberUnion,
    ChatMemberBanned,
    ChatMemberRestricted,
)


class BotPermissionService:
    """
    Сервис для проверки прав бота и пользователей в чатах.

    Отвечает за:
    - Проверку прав бота на модерацию
    - Проверку статуса администратора пользователя
    """

    def __init__(self, bot: Bot):
        self.bot = bot

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
        Проверяет, может ли бот модерировать чат.

        Бот может модерировать, если он:
        - Является администратором или владельцем
        - Имеет право can_restrict_members

        Args:
            chat_tgid: Telegram ID чата

        Returns:
            True если бот может модерировать
        """
        member = await self.get_bot_member(chat_tgid=chat_tgid)

        if isinstance(member, (ChatMemberOwner, ChatMemberAdministrator)):
            return member.can_restrict_members
        return False

    async def can_delete_messages(self, chat_tgid: ChatIdUnion) -> bool:
        """
        Проверяет, может ли бот удалять сообщения в чате.

        Args:
            chat_tgid: Telegram ID чата

        Returns:
            True если бот может удалять сообщения
        """
        member = await self.get_bot_member(chat_tgid=chat_tgid)

        if isinstance(member, (ChatMemberOwner, ChatMemberAdministrator)):
            return member.can_delete_messages
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
