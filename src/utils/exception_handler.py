import logging
from typing import Optional

from aiogram.types import Message

from exceptions.base import BotBaseException
from utils.send_message import send_html_message_with_kb

logger = logging.getLogger(__name__)


async def handle_exception(
    message: Message, exc: Exception, context: Optional[str] = None
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
