"""Кодирование callback для кнопки «Заблокировать» в карточке автомодерации."""

from constants.callback import CallbackData
from utils.antibot_utils import decode_antibot_params, encode_antibot_params


def encode_automod_block_callback(work_chat_tgid: str, violator_user_id: int) -> str:
    """Собирает callback_data для бана (лимит Telegram64 байта)."""
    payload = encode_antibot_params(work_chat_tgid, violator_user_id)
    return f"{CallbackData.AutoModeration.BLOCK_PREFIX}{payload}"


def decode_automod_block_callback(data: str) -> tuple[str | None, int | None]:
    """Извлекает work_chat_tgid и user_id из callback_data кнопки «Заблокировать»."""
    prefix = CallbackData.AutoModeration.BLOCK_PREFIX
    if not data.startswith(prefix):
        return None, None
    return decode_antibot_params(data.removeprefix(prefix))
