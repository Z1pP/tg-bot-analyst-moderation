from models import ChatMessage


def format_messages_for_llm(messages: list[ChatMessage]) -> str:
    """
    Превращает список объектов сообщений в строку вида:
    [User1]: Ребят, когда деплой?
    [Admin]: Завтра в 12:00.
    """
    buffer = []
    for msg in messages:
        # Фильтрация мусора
        if not msg.text or len(msg.text) < 3:
            continue
        if msg.text.startswith("/"):  # Игнорируем команды
            continue

        clean_text = msg.text[:500]

        user_name = msg.username or "Unknown"

        buffer.append(f"[{user_name}]: {clean_text}")

    return "\n".join(buffer)
