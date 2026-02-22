import logging
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

    def _format_error_message_for_dev(
        self, event: TelegramObject, exc: Exception
    ) -> str:
        """Формирует детальное сообщение об ошибке для отправки DEV-пользователям."""
        exc_type = type(exc).__name__
        exc_msg = str(exc) or "(без сообщения)"
        tb = traceback.format_exc()
        event_info = self._get_event_info(event)
        body = (
            f"<b>🔴 Ошибка бота</b>\n\n"
            f"<b>Тип:</b> {escape(exc_type)}\n"
            f"<b>Сообщение:</b> {escape(exc_msg)}\n\n"
            f"<b>Где:</b> {escape(event_info)}\n\n"
            f"<pre>{escape(tb)}</pre>"
        )
        if len(body) > TELEGRAM_MESSAGE_MAX_LENGTH:
            body = body[: TELEGRAM_MESSAGE_MAX_LENGTH - 50] + "\n\n… (обрезано)"
        return body

    def _get_event_info(self, event: TelegramObject) -> str:
        """Краткое описание события для отчёта об ошибке."""
        if isinstance(event, Message):
            return f"Message, chat_id={event.chat.id}, from_user_id={event.from_user.id if event.from_user else None}"
        if isinstance(event, CallbackQuery):
            return (
                f"CallbackQuery, data={event.data!r}, "
                f"from_user_id={event.from_user.id if event.from_user else None}"
            )
        return type(event).__name__

    async def _notify_devs_about_error(
        self, event: TelegramObject, exc: Exception
    ) -> None:
        """Отправляет детальную информацию об ошибке всем пользователям с ролью DEV в личку."""
        try:
            dev_users = await self.user_repository.get_users_with_role(UserRole.DEV)
        except Exception as e:
            logger.error(
                "Не удалось получить список DEV для уведомления об ошибке: %s",
                e,
                exc_info=True,
            )
            return
        if not dev_users:
            return
        text = self._format_error_message_for_dev(event, exc)
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
                )

    def _get_user_id(self, event: TelegramObject) -> int | None:
        if isinstance(event, (Message, CallbackQuery)):
            return event.from_user.id
        return None

    def _get_chat_id(self, event: TelegramObject) -> int | None:
        if isinstance(event, CallbackQuery):
            if event.message:
                return event.message.chat.id
        elif isinstance(event, Message):
            return event.chat.id
        return None
