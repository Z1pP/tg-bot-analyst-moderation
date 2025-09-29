import logging
from datetime import timedelta
from typing import Union

from aiogram import Bot
from aiogram.types import ChatPermissions

ChatIdUnion = Union[int, str]
logger = logging.getLogger(__name__)


class BotMessageService:
    """Сервис для управления сообщениями в боте"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_private_message(self, user_tgid: ChatIdUnion, text: str) -> None:
        try:
            await self.bot.send_message(
                chat_id=user_tgid,
                text=text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(
                (
                    "Произошла ошибка при отправке сообщения отправить сообщение "
                    "пользователю с Telegram ID %s: %s"
                ),
                user_tgid,
                e,
            )
            return None

    async def send_chat_message(self, chat_tgid: ChatIdUnion, text: str) -> None:
        try:
            await self.bot.send_message(
                chat_id=chat_tgid,
                text=text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(
                "Произошла ошибка при отправке сообщения в чат с Telegram ID %s: %s",
                chat_tgid,
                e,
            )
            return None

    async def forward_message(
        self,
        chat_tgid: ChatIdUnion,
        from_chat_tgid: ChatIdUnion,
        message_tgid: int,
    ) -> None:
        try:
            await self.bot.forward_message(
                chat_id=chat_tgid,
                from_chat_id=from_chat_tgid,
                message_id=message_tgid,
            )
        except Exception as e:
            logger.error("Не удалось скопировать сообщение в чат %s: %s", chat_tgid, e)
            return None

    async def delete_message_from_chat(
        self,
        chat_id: ChatIdUnion,
        message_id: int,
    ) -> None:
        try:
            await self.bot.delete_message(
                chat_id=chat_id,
                message_id=message_id,
            )
        except Exception as e:
            logger.error("Не удалось удалить сообщение в чате %s: %s", chat_id, e)
            return None

    async def mute_chat_member(
        self,
        chat_id: ChatIdUnion,
        user_id: int,
        until_date: timedelta,
    ) -> None:
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
        )
        try:
            await self.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=permissions,
                until_date=until_date,
            )
        except Exception as e:
            logger.error(
                "Не удалось замьютить пользователя %s в чате %s: %s",
                user_id,
                chat_id,
                e,
            )
            return None

    async def ban_chat_member(self, chat_id: ChatIdUnion, user_id: int) -> None:
        try:
            await self.bot.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id,
            )
        except Exception as e:
            logger.error(
                "Не удалось забанить пользователя %s в чате %s: %s", user_id, chat_id, e
            )
            return None
