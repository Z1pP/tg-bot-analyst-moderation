import logging
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import ChatIdUnion, ChatPermissions, InlineKeyboardMarkup

from constants.punishment import PunishmentType
from exceptions.moderation import MessageTooOldError
from services.permissions import BotPermissionService
from services.time_service import TimeZoneService

logger = logging.getLogger(__name__)


class BotMessageService:
    """
    Сервис для управления сообщениями и применения наказаний в Telegram.

    Отвечает за:
    - Отправку сообщений в чаты и личные сообщения
    - Пересылку сообщений
    - Удаление сообщений
    - Применение наказаний (mute/ban)

    Автоматически проверяет права бота перед выполнением действий.
    """

    def __init__(
        self,
        bot: Bot,
        permission_service: BotPermissionService,
    ):
        self.bot = bot
        self.permission_service = permission_service

    async def send_private_message(
        self,
        user_tgid: ChatIdUnion,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> None:
        """
        Отправляет личное сообщение пользователю.

        Args:
            user_tgid: Telegram ID пользователя
            text: Текст сообщения (HTML)
            reply_markup: Опциональная клавиатура
        """
        try:
            await self.bot.send_message(
                chat_id=user_tgid,
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
        except TelegramAPIError as e:
            logger.error(
                "Ошибка Telegram API при отправке сообщения пользователю %s: %s",
                user_tgid,
                e,
            )
        except Exception:
            logger.exception(
                "Неожиданная ошибка при отправке сообщения пользователю %s",
                user_tgid,
            )

    async def send_chat_message(self, chat_tgid: ChatIdUnion, text: str) -> None:
        """
        Отправляет сообщение в чат.

        Проверяет право can_post_messages перед отправкой.

        Args:
            chat_tgid: Telegram ID чата
            text: Текст сообщения (HTML)
        """
        can_post = await self.permission_service.can_post_messages(chat_tgid=chat_tgid)
        if not can_post:
            logger.warning(
                "Бот не может отправлять сообщения в чат %s. Пропуск отправки.",
                chat_tgid,
            )
            return

        try:
            await self.bot.send_message(
                chat_id=chat_tgid,
                text=text,
                parse_mode="HTML",
            )
        except TelegramAPIError as e:
            logger.error(
                "Ошибка Telegram API при отправке сообщения в чат %s: %s",
                chat_tgid,
                e,
            )
        except Exception:
            logger.exception(
                "Неожиданная ошибка при отправке сообщения в чат %s",
                chat_tgid,
            )

    async def copy_message(
        self,
        chat_tgid: ChatIdUnion,
        from_chat_tgid: ChatIdUnion,
        message_id: int,
    ) -> Optional[int]:
        """
        Копирует сообщение в чат.

        Args:
            chat_tgid: Telegram ID чата-получателя
            from_chat_tgid: Telegram ID чата-источника
            message_id: ID сообщения для копирования

        Returns:
            ID отправленного сообщения или None при ошибке
        """
        try:
            result = await self.bot.copy_message(
                chat_id=chat_tgid,
                from_chat_id=from_chat_tgid,
                message_id=message_id,
            )
            return result.message_id
        except Exception as e:
            logger.error(
                "Не удалось скопировать сообщение в чат %s: %s",
                chat_tgid,
                e,
            )
            return None

    async def copy_message_as_reply(
        self,
        chat_tgid: ChatIdUnion,
        from_chat_tgid: ChatIdUnion,
        message_id: int,
        reply_to_message_id: int,
    ) -> Optional[int]:
        """
        Копирует сообщение как ответ на другое сообщение.

        Args:
            chat_tgid: Telegram ID чата-получателя
            from_chat_tgid: Telegram ID чата-источника
            message_id: ID сообщения для копирования
            reply_to_message_id: ID сообщения, на которое отвечаем

        Returns:
            ID отправленного сообщения или None при ошибке
        """
        try:
            result = await self.bot.copy_message(
                chat_id=chat_tgid,
                from_chat_id=from_chat_tgid,
                message_id=message_id,
                reply_to_message_id=reply_to_message_id,
            )
            return result.message_id
        except Exception as e:
            logger.error(
                "Не удалось скопировать сообщение %s из чата %s в чат %s: %s",
                message_id,
                from_chat_tgid,
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
        """
        Пересылает сообщение из одного чата в другой.

        Args:
            chat_tgid: Telegram ID чата-получателя
            from_chat_tgid: Telegram ID чата-источника
            message_tgid: ID сообщения
        """
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
        message_date: Optional[datetime] = None,
    ) -> bool:
        """
        Удаляет сообщение из чата.

        Проверяет возраст сообщения - Telegram не позволяет
        удалять сообщения старше 48 часов.
        Проверяет право can_delete_messages перед удалением.

        Args:
            chat_id: Telegram ID чата
            message_id: ID сообщения
            message_date: Дата сообщения (для проверки возраста)

        Returns:
            True если удаление успешно

        Raises:
            MessageTooOldError: Если сообщение старше 48 часов
        """
        can_delete = await self.permission_service.can_delete_messages(
            chat_tgid=chat_id
        )
        if not can_delete:
            logger.warning(
                "Bot cannot delete messages in chat %s. Skipping deletion.",
                chat_id,
            )
            return False

        if message_date:
            now_local = TimeZoneService.now()
            if now_local - message_date > timedelta(hours=48):
                raise MessageTooOldError()

        try:
            return await self.bot.delete_message(
                chat_id=chat_id,
                message_id=message_id,
            )
        except Exception as e:
            logger.error("Не удалось удалить сообщение в чате %s: %s", chat_id, e)
            return False

    async def apply_punishment(
        self,
        chat_tg_id: ChatIdUnion,
        user_tg_id: ChatIdUnion,
        *,
        action: PunishmentType,
        duration_seconds: Optional[int] = None,
    ) -> bool:
        """
        Применяет наказание к пользователю в чате.

        Проверяет право can_moderate перед применением MUTE/BAN.

        Args:
            chat_tg_id: Telegram ID чата
            user_tg_id: Telegram ID пользователя
            action: Тип наказания (MUTE/BAN/WARNING)
            duration_seconds: Длительность для MUTE

        Returns:
            True если наказание применено успешно
        """
        # Проверка прав для действий, требующих модерации
        if action in (PunishmentType.MUTE, PunishmentType.BAN):
            can_moderate = await self.permission_service.can_moderate(
                chat_tgid=chat_tg_id
            )
            if not can_moderate:
                logger.warning(
                    "Bot cannot moderate in chat %s. Skipping punishment %s for user %s.",
                    chat_tg_id,
                    action,
                    user_tg_id,
                )
                return False

        try:
            if action == PunishmentType.MUTE:
                return await self.mute_chat_member(
                    chat_tg_id=chat_tg_id,
                    user_tg_id=int(user_tg_id),
                    duration_seconds=duration_seconds,
                )
            elif action == PunishmentType.BAN:
                return await self.ban_chat_member(
                    chat_tg_id=chat_tg_id,
                    user_tg_id=int(user_tg_id),
                )
            elif action == PunishmentType.WARNING:
                return True
            else:
                raise ValueError(f"Неизвестное действие: {action}")
        except Exception as e:
            logger.error(
                "Не удалось применить наказание %s к пользователю %s в чате %s: %s",
                action,
                user_tg_id,
                chat_tg_id,
                e,
            )
            return False

    async def mute_chat_member(
        self,
        chat_tg_id: ChatIdUnion,
        user_tg_id: int,
        duration_seconds: int,
    ) -> bool:
        """
        Ограничивает права пользователя в чате (mute).

        Проверяет право can_moderate перед применением.

        Args:
            chat_tg_id: Telegram ID чата
            user_tg_id: Telegram ID пользователя
            duration_seconds: Длительность мьюта в секундах

        Returns:
            True если мьют применен успешно
        """
        can_moderate = await self.permission_service.can_moderate(chat_tgid=chat_tg_id)
        if not can_moderate:
            logger.warning(
                "Bot cannot moderate in chat %s. Skipping mute for user %s.",
                chat_tg_id,
                user_tg_id,
            )
            return False

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
            return await self.bot.restrict_chat_member(
                chat_id=chat_tg_id,
                user_id=user_tg_id,
                permissions=permissions,
                until_date=timedelta(seconds=duration_seconds),
            )
        except Exception as e:
            logger.error(
                "Не удалось замьютить пользователя %s в чате %s: %s",
                user_tg_id,
                chat_tg_id,
                e,
            )
            return False

    async def ban_chat_member(
        self,
        chat_tg_id: ChatIdUnion,
        user_tg_id: int,
    ) -> bool:
        """
        Банит пользователя в чате бессрочно.

        Проверяет право can_moderate перед применением.

        Args:
            chat_tg_id: Telegram ID чата
            user_tg_id: Telegram ID пользователя

        Returns:
            True если бан применен успешно
        """
        can_moderate = await self.permission_service.can_moderate(chat_tgid=chat_tg_id)
        if not can_moderate:
            logger.warning(
                "Bot cannot moderate in chat %s. Skipping ban for user %s.",
                chat_tg_id,
                user_tg_id,
            )
            return False

        try:
            return await self.bot.ban_chat_member(
                chat_id=chat_tg_id,
                user_id=user_tg_id,
            )
        except Exception as e:
            logger.error(
                "Не удалось забанить пользователя %s в чате %s: %s",
                user_tg_id,
                chat_tg_id,
                e,
            )
            return False

    async def unban_chat_member(
        self,
        chat_tg_id: ChatIdUnion,
        user_tg_id: int,
    ) -> bool:
        """
        Разбанивает пользователя в чате.

        Проверяет право can_moderate перед применением.

        Args:
            chat_tg_id: Telegram ID чата
            user_tg_id: Telegram ID пользователя

        Returns:
            True если разбан применен успешно
        """
        can_moderate = await self.permission_service.can_moderate(chat_tgid=chat_tg_id)
        if not can_moderate:
            logger.warning(
                "Bot cannot moderate in chat %s. Skipping unban for user %s.",
                chat_tg_id,
                user_tg_id,
            )
            return False

        try:
            return await self.bot.unban_chat_member(
                chat_id=chat_tg_id,
                user_id=user_tg_id,
                only_if_banned=True,
            )
        except Exception as e:
            logger.error(
                "Не удалось разбанить пользователя %s в чате %s: %s",
                user_tg_id,
                chat_tg_id,
                e,
            )
            return False

    async def unmute_chat_member(
        self,
        chat_tg_id: ChatIdUnion,
        user_tg_id: int,
    ) -> bool:
        """
        Размьютит пользователя в чате.

        Проверяет право can_moderate перед применением.

        Args:
            chat_tg_id: Telegram ID чата
            user_tg_id: Telegram ID пользователя

        Returns:
            True если размьют применен успешно
        """
        can_moderate = await self.permission_service.can_moderate(chat_tgid=chat_tg_id)
        if not can_moderate:
            logger.warning(
                "Bot cannot moderate in chat %s. Skipping unmute for user %s.",
                chat_tg_id,
                user_tg_id,
            )
            return False

        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True,
        )
        try:
            return await self.bot.restrict_chat_member(
                chat_id=chat_tg_id,
                user_id=user_tg_id,
                permissions=permissions,
            )
        except Exception as e:
            logger.error(
                "Не удалось размьютить пользователя %s в чате %s: %s",
                user_tg_id,
                chat_tg_id,
                e,
            )
            return False

    async def get_chat_invite_link(
        self,
        chat_tgid: ChatIdUnion,
    ) -> Optional[str]:
        """
        Получает invite ссылку на чат.

        Проверяет право can_invite_users перед получением ссылки.

        Args:
            chat_tgid: Telegram ID чата

        Returns:
            Invite ссылка или None при ошибке
        """
        can_invite = await self.permission_service.can_invite_users(chat_tgid=chat_tgid)
        if not can_invite:
            logger.warning(
                "Bot cannot invite users in chat %s. Skipping invite link request.",
                chat_tgid,
            )
            return None

        try:
            result = await self.bot.export_chat_invite_link(chat_id=chat_tgid)
            # В aiogram 3.x метод возвращает ChatInviteLink объект с атрибутом invite_link
            if hasattr(result, "invite_link"):
                return result.invite_link
            # Если вернулась строка напрямую (старые версии или другой формат)
            if isinstance(result, str):
                return result
            # Fallback: пытаемся получить из атрибута
            return getattr(result, "invite_link", None)
        except Exception as e:
            logger.error(
                "Не удалось получить invite ссылку для чата %s: %s",
                chat_tgid,
                e,
            )
            return None
