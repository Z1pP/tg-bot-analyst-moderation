# Хелперы для use cases амнистии (общая логика проверок через Telegram API).

import logging
from typing import Awaitable, TypeVar

from aiogram.exceptions import TelegramAPIError

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def safe_telegram_check(
    coro: Awaitable[T],
    default: T,
    log_message: str,
    *log_args: object,
) -> T:
    """
    Выполняет корутину (например, проверку через Bot API) и при TelegramAPIError
    логирует предупреждение и возвращает значение по умолчанию.
    """
    try:
        return await coro
    except TelegramAPIError as e:
        logger.warning(log_message, *log_args, e)
        return default
