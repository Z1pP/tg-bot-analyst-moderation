"""Публичные ссылки на сообщения в группах/супергруппах (t.me/c/...)."""


def public_group_message_link(chat_tgid: str, message_id: int) -> str:
    """Формирует https://t.me/c/<id>/<message_id> для чата с отрицательным tg id."""
    cid = str(chat_tgid)
    if cid.startswith("-100"):
        inner = cid[4:]
    elif cid.startswith("-"):
        inner = cid[1:]
    else:
        inner = cid
    return f"https://t.me/c/{inner}/{message_id}"
