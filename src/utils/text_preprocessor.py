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
    # Чтобы соблюсти хронологию и лимит, идем по списку (там уже reversed, т.е. от новых)
    for msg in messages:
        # Фильтрация мусора
        if not msg.text or len(msg.text) < 3:
            continue
        if msg.text.startswith("/"):  # Игнорируем команды
            continue

        clean_text = msg.text[:500]
        user_name = msg.username or "Unknown"

        formatted_line = f"[{user_name}]: {clean_text}"
        line_len = len(formatted_line) + 1

        if current_chars + line_len > max_chars:
            break

        buffer.append(formatted_line)
        current_chars += line_len
        count += 1

    # Возвращаем в хронологическом порядке (старые в начале)
    return "\n".join(reversed(buffer)), count
