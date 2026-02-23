"""
Аутентификация Telegram Mini App через initData.

Telegram подписывает initData HMAC-SHA256:
  secret_key = HMAC-SHA256("WebAppData", BOT_TOKEN)
  hash = HMAC-SHA256(data_check_string, secret_key)

data_check_string — все поля initData (кроме hash), отсортированные по ключу,
соединённые символом '\n'.
"""

import hashlib
import hmac
import json
import logging
import time
from typing import Annotated
from urllib.parse import parse_qsl, unquote

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from config import settings

logger = logging.getLogger(__name__)

INIT_DATA_HEADER = APIKeyHeader(name="X-Telegram-Init-Data", auto_error=False)

MAX_AGE_SECONDS = 3600


def _compute_secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()


def _verify_init_data(raw: str) -> dict:
    """
    Проверяет подпись initData и возвращает распарсенные поля.
    Raises HTTPException при невалидных или устаревших данных.
    """
    params = dict(parse_qsl(raw, keep_blank_values=True))
    received_hash = params.pop("hash", None)

    if not received_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing hash in initData",
        )

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))

    secret_key = _compute_secret_key(settings.BOT_TOKEN)
    expected_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid initData signature",
        )

    auth_date = int(params.get("auth_date", 0))
    if not settings.IS_DEVELOPMENT and time.time() - auth_date > MAX_AGE_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="initData expired",
        )

    return params


def verify_telegram_init_data(
    raw_init_data: Annotated[str | None, Depends(INIT_DATA_HEADER)],
) -> dict:
    """
    FastAPI dependency. Возвращает распарсенные поля initData.
    В dev-режиме пропускает проверку подписи если заголовок отсутствует.
    """
    if not raw_init_data:
        if settings.IS_DEVELOPMENT:
            logger.warning("Dev mode: initData header missing, skipping auth")
            return {"user": '{"id":0,"first_name":"Dev","username":"dev_user"}'}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Telegram-Init-Data header required",
        )

    return _verify_init_data(unquote(raw_init_data))


TelegramInitData = Annotated[dict, Depends(verify_telegram_init_data)]


def tg_id_from_init_data(init_data: dict) -> str:
    """Извлекает tg_id пользователя из распарсенных полей initData."""
    user_raw = init_data.get("user", "{}")
    try:
        user = json.loads(user_raw) if isinstance(user_raw, str) else user_raw
        return str(user.get("id", "0"))
    except Exception:
        return "0"


def username_from_init_data(init_data: dict) -> str:
    """Извлекает username пользователя из распарсенных полей initData."""
    user_raw = init_data.get("user", "{}")
    try:
        user = json.loads(user_raw) if isinstance(user_raw, str) else user_raw
        return user.get("username", "")
    except Exception:
        return ""
