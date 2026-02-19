"""Общие хелперы обработки ошибок в хендлерах."""

from __future__ import annotations

import logging
from typing import Any

from exceptions import BusinessLogicException


def raise_business_logic(
    log_message: str,
    user_message: str,
    exc: BaseException,
    log: logging.Logger,
    *log_args: Any,
) -> None:
    """
    Логирует исключение и пробрасывает BusinessLogicException с сообщением для пользователя.

    Args:
        log_message: Сообщение для лога (и шаблон при наличии log_args).
        user_message: Текст для пользователя (get_user_message()).
        exc: Исходное исключение (будет в __cause__).
        log: Логгер для записи.
        *log_args: Аргументы для подстановки в log_message.
    """
    log.exception(log_message, *log_args, exc_info=exc)
    raise BusinessLogicException(
        message=user_message,
        details={"original": str(exc)},
    ) from exc
