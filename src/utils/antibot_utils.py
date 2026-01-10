def encode_antibot_params(chat_id: str, user_id: int) -> str:
    """
    Кодирует chat_id и user_id в строку для deep link.
    Заменяет '-' на 'm' для совместимости с параметрами Telegram.
    """
    safe_chat_id = chat_id.replace("-", "m")
    return f"v_{safe_chat_id}_{user_id}"


def decode_antibot_params(payload: str) -> tuple[str, int] | tuple[None, None]:
    """
    Декодирует строку параметров обратно в chat_id и user_id.
    """
    try:
        parts = payload.split("_")
        if len(parts) != 3 or parts[0] != "v":
            return None, None

        safe_chat_id = parts[1]
        user_id = int(parts[2])
        chat_id = safe_chat_id.replace("m", "-")
        return chat_id, user_id
    except (ValueError, IndexError):
        return None, None
