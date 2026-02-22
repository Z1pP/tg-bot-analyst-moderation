import asyncio
import hashlib
import logging
import time
import traceback
from html import escape
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import CallbackQuery, Message, TelegramObject
from punq import Container

from constants.enums import UserRole
from exceptions.base import BotBaseException
from exceptions.moderation import PrivateModerationError, PublicModerationError
from keyboards.inline.chats import hide_notification_ikb
from repositories.user_repository import UserRepository
from services import BotMessageService
from utils.send_message import send_html_message_with_kb

logger = logging.getLogger(__name__)

# Лимит длины текста сообщения в Telegram
TELEGRAM_MESSAGE_MAX_LENGTH = 4096

# Кеш DEV-пользователей обновляется раз в 5 минут
_DEV_CACHE_TTL = 300

# Одинаковая ошибка уведомляет DEV не чаще одного раза в 60 секунд
_DEV_NOTIFY_COOLDOWN = 60


def _make_error_key(exc: Exception) -> str:
    """Формирует уникальный ключ ошибки для rate limiting."""
    tb = traceback.format_exc()
    raw = f"{type(exc).__name__}:{tb[:400]}"
    return hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()


def _format_dev_error_text(exc: Exception, context: str) -> str:
    """Формирует детальное HTML-сообщение об ошибке для DEV-пользователей."""
    exc_type = type(exc).__name__
    exc_msg = str(exc) or "(без сообщения)"
    tb = traceback.format_exc()
    body = (
        f"<b>🔴 Ошибка бота</b>\n\n"
        f"<b>Тип:</b> {escape(exc_type)}\n"
        f"<b>Сообщение:</b> {escape(exc_msg)}\n\n"
        f"<b>Где:</b> {escape(context)}\n\n"
        f"<pre>{escape(tb)}</pre>"
    )
    if len(body) > TELEGRAM_MESSAGE_MAX_LENGTH:
        body = body[: TELEGRAM_MESSAGE_MAX_LENGTH - 50] + "\n\n… (обрезано)"
    return body


async def notify_devs_about_error(
    bot_message_service: BotMessageService,
    user_repository: UserRepository,
    exc: Exception,
    context: str = "",
) -> None:
    """
    Отправляет детальное уведомление об ошибке всем DEV-пользователям.

    Предназначена для вызова из фоновых процессов (планировщики, задачи),
    где нет доступа к экземпляру AsyncErrorHandler.

    Args:
        bot_message_service: Сервис отправки сообщений.
        user_repository: Репозиторий для получения DEV-пользователей.
        exc: Пойманное исключение.
        context: Текстовое описание места возникновения ошибки.
    """
    try:
        dev_users = await user_repository.get_users_with_role(UserRole.DEV)
    except Exception as e:
        logger.error(
            "Не удалось получить список DEV для уведомления: %s", e, exc_info=True
        )
        return

    if not dev_users:
        return

    text = _format_dev_error_text(exc, context)

    for user in dev_users:
        if not user.tg_id:
            continue
        try:
            await bot_message_service.send_private_message(
                user_tgid=user.tg_id,
                text=text,
            )
        except Exception as e:
            logger.warning(
                "Не удалось отправить уведомление об ошибке DEV %s: %s",
                user.tg_id,
                e,
                exc_info=True,
            )


async def handle_exception(
    message: Message,
    exc: Exception,
    context: Optional[str] = None,
) -> None:
    """
    Обрабатывает исключения и отправляет соответствующее сообщение пользователю.

    Args:
        message: Объект сообщения для ответа
        exc: Исключение, которое нужно обработать
        context: Контекст, в котором произошло исключение (например, имя функции)
    """
    if isinstance(exc, BotBaseException):
        logger.warning(
            f"Обработано исключение{' в ' + context if context else ''}: {exc}",
            exc_info=True,
        )
        await send_html_message_with_kb(
            message=message,
            text=exc.get_user_message(),
            reply_markup=hide_notification_ikb(),
        )
    else:
        logger.error(
            f"Необработанное исключение{' в ' + context if context else ''}: {exc}",
            exc_info=True,
        )
        await send_html_message_with_kb(
            message=message,
            text="❌ Произошла непредвиденная ошибка. Попробуйте позже.",
            reply_markup=hide_notification_ikb(),
        )


def registry_exceptions(dispatcher: Dispatcher, container: Container) -> None:
    # Messages
    dispatcher.message.middleware(container.resolve(AsyncErrorHandler))
    # Callbacks
    dispatcher.callback_query.middleware(container.resolve(AsyncErrorHandler))


class AsyncErrorHandler(BaseMiddleware):
    def __init__(
        self,
        bot_message_service: BotMessageService,
        user_repository: UserRepository,
    ):
        self.bot_message_service = bot_message_service
        self.user_repository = user_repository

        # Rate limiting: не спамить DEV одинаковой ошибкой
        self._error_last_sent: dict[str, float] = {}
        self._error_cooldown_lock = asyncio.Lock()

        # Кеш DEV-пользователей внутри инстанса
        self._dev_users_cache: Optional[list] = None
        self._dev_users_cache_until: float = 0.0
        self._dev_users_cache_lock = asyncio.Lock()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except PrivateModerationError as e:
            logger.info("Обработано PrivateModerationError: %s", e)
            user_message = e.get_user_message()
            user_id = self._get_user_id(event)
            if user_id:
                await self.bot_message_service.send_private_message(
                    user_tgid=user_id,
                    text=user_message,
                )
            return None
        except PublicModerationError as e:
            logger.info("Обработано PublicModerationError: %s", e)
            user_message = e.get_user_message()
            chat_id = self._get_chat_id(event)
            if chat_id:
                await self.bot_message_service.send_chat_message(
                    chat_tgid=chat_id,
                    text=user_message,
                )
            return None
        except BotBaseException as e:
            logger.warning("Обработано BotBaseException: %s", e)
            user_message = e.get_user_message()
            chat_id = self._get_chat_id(event)
            user_id = self._get_user_id(event)
            if chat_id:
                await self.bot_message_service.send_chat_message(
                    chat_tgid=chat_id,
                    text=user_message,
                )
            elif user_id:
                await self.bot_message_service.send_private_message(
                    user_tgid=user_id,
                    text=user_message,
                )
            return None
        except Exception as e:
            logger.error("Необработанное исключение: %s", e, exc_info=True)
            await self._notify_devs_about_error(event, e)
            raise

    async def _should_notify_dev(self, exc: Exception) -> bool:
        """Проверяет rate limiting: одна и та же ошибка не чаще раза в 60 сек."""
        key = _make_error_key(exc)
        async with self._error_cooldown_lock:
            now = time.monotonic()
            if now - self._error_last_sent.get(key, 0.0) < _DEV_NOTIFY_COOLDOWN:
                return False
            self._error_last_sent[key] = now
            return True

    async def _get_dev_users(self) -> list:
        """Возвращает DEV-пользователей с кешированием на 5 минут."""
        async with self._dev_users_cache_lock:
            now = time.monotonic()
            if self._dev_users_cache is not None and now < self._dev_users_cache_until:
                return self._dev_users_cache
            try:
                users = await self.user_repository.get_users_with_role(UserRole.DEV)
                self._dev_users_cache = users
                self._dev_users_cache_until = now + _DEV_CACHE_TTL
                return users
            except Exception as e:
                logger.error("Не удалось получить список DEV: %s", e, exc_info=True)
                return self._dev_users_cache or []

    def _get_event_context(self, event: TelegramObject) -> str:
        """Краткое описание события для отчёта об ошибке."""
        if isinstance(event, Message):
            from_id = event.from_user.id if event.from_user else None
            return f"Message, chat_id={event.chat.id}, from_user_id={from_id}"
        if isinstance(event, CallbackQuery):
            from_id = event.from_user.id if event.from_user else None
            return f"CallbackQuery, data={event.data!r}, from_user_id={from_id}"
        return type(event).__name__

    async def _notify_devs_about_error(
        self, event: TelegramObject, exc: Exception
    ) -> None:
        """Отправляет детальную информацию об ошибке всем DEV-пользователям."""
        if not await self._should_notify_dev(exc):
            logger.debug(
                "Уведомление DEV подавлено rate limiting для ошибки %s",
                type(exc).__name__,
            )
            return

        dev_users = await self._get_dev_users()
        if not dev_users:
            return

        context = self._get_event_context(event)
        text = _format_dev_error_text(exc, context)

        for user in dev_users:
            if not user.tg_id:
                continue
            try:
                await self.bot_message_service.send_private_message(
                    user_tgid=user.tg_id,
                    text=text,
                )
            except Exception as e:
                logger.warning(
                    "Не удалось отправить уведомление об ошибке DEV %s: %s",
                    user.tg_id,
                    e,
                    exc_info=True,
                )

    def _get_user_id(self, event: TelegramObject) -> int | None:
        if isinstance(event, (Message, CallbackQuery)):
            return event.from_user.id if event.from_user else None
        return None

    def _get_chat_id(self, event: TelegramObject) -> int | None:
        if isinstance(event, CallbackQuery):
            if event.message:
                return event.message.chat.id
        elif isinstance(event, Message):
            return event.chat.id
        return None
