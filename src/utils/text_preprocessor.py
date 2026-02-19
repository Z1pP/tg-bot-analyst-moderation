def format_messages_for_llm(messages: list, max_chars: int = 100000) -> tuple[str, int]:
    """
    Превращает список объектов сообщений в строку вида:
    [User1]: Ребят, когда деплой?
    [Admin]: Завтра в 12:00.
    """
    buffer = []
    current_chars = 0
    count = 0

    # Сообщения приходят от новых к старым (из репозитория reversed)
    # Поддерживаются кортежи (text, username) и объекты с .text / .username
    for msg in messages:
        if isinstance(msg, tuple) and len(msg) >= 2:
            text, user_name = msg[0], (msg[1] or "Unknown")
        else:
            text = getattr(msg, "text", None)
            user_name = getattr(msg, "username", None) or "Unknown"

        # Фильтрация мусора
        if not text or len(text) < 3:
            continue
        if text.startswith("/"):  # Игнорируем команды
            continue

        clean_text = text[:500]

        formatted_line = f"[{user_name}]: {clean_text}"
        line_len = len(formatted_line) + 1

        if current_chars + line_len > max_chars:
            break

        buffer.append(formatted_line)
        current_chars += line_len
        count += 1

    # Возвращаем в хронологическом порядке (старые в начале)
    return "\n".join(reversed(buffer)), count
