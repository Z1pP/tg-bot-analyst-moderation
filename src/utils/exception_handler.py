import logging
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import CallbackQuery, Message, TelegramObject

from container import container
from exceptions.base import BotBaseException
from exceptions.moderation import PrivateModerationError, PublicModerationError
from services import BotMessageService
from utils.send_message import send_html_message_with_kb

logger = logging.getLogger(__name__)


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
        await send_html_message_with_kb(message=message, text=exc.get_user_message())
    else:
        logger.error(
            f"Необработанное исключение{' в ' + context if context else ''}: {exc}",
            exc_info=True,
        )
        await send_html_message_with_kb(
            message=message,
            text="❌ Произошла непредвиденная ошибка. Попробуйте позже.",
        )


def registry_exceptions(dispatcher: Dispatcher) -> None:
    # Messages
    dispatcher.message.middleware(container.resolve(AsyncErrorHandler))
    # Callbacks
    dispatcher.callback_query.middleware(container.resolve(AsyncErrorHandler))


class AsyncErrorHandler(BaseMiddleware):
    def __init__(self, bot_message_service: BotMessageService):
        self.bot_message_service = bot_message_service

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
        except Exception as e:
            logger.error("Необработанное исключение: %s", e, exc_info=True)
            raise

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
