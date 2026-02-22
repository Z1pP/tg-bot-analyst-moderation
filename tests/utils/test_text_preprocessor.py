"""Тесты для utils/text_preprocessor.py."""

from utils.text_preprocessor import format_messages_for_llm


def test_format_messages_for_llm_tuples() -> None:
    """Форматирование списка кортежей (text, username). Возврат в хронологическом порядке (старые в начале)."""
    messages = [
        ("Привет", "User1"),
        ("Ответ", "Admin"),
    ]
    text, count = format_messages_for_llm(messages)
    assert count == 2
    assert "[User1]: Привет" in text
    assert "[Admin]: Ответ" in text
    # Сообщения приходят от новых к старым, после reversed старые в начале
    assert text.index("[Admin]") < text.index("[User1]")


def test_format_messages_for_llm_objects() -> None:
    """Форматирование объектов с атрибутами text и username. Текст короче 3 символов пропускается."""

    class Msg:
        def __init__(self, text: str, username: str | None):
            self.text = text
            self.username = username

    messages = [
        Msg("Hello", "Alice"),
        Msg("Hi there", None),
    ]
    text, count = format_messages_for_llm(messages)
    assert count == 2
    assert "[Alice]: Hello" in text
    assert "[Unknown]: Hi there" in text


def test_format_messages_for_llm_skips_short() -> None:
    """Сообщения короче 3 символов пропускаются."""
    messages = [("Hi", "U1"), ("Hello world", "U2")]
    text, count = format_messages_for_llm(messages)
    assert "Hi" not in text
    assert "[U2]: Hello world" in text
    assert count == 1


def test_format_messages_for_llm_skips_commands() -> None:
    """Сообщения, начинающиеся с /, пропускаются."""
    messages = [("/start", "Bot"), ("Normal text", "User")]
    text, count = format_messages_for_llm(messages)
    assert "/start" not in text
    assert "[User]: Normal text" in text
    assert count == 1


def test_format_messages_for_llm_skips_empty_text() -> None:
    """Сообщения без текста и короче 3 символов пропускаются."""
    messages = [("", "U1"), ("Okay", "U2")]
    text, count = format_messages_for_llm(messages)
    assert count == 1
    assert "[U2]: Okay" in text


def test_format_messages_for_llm_max_chars() -> None:
    """Ограничение по max_chars обрезает вывод."""
    messages = [("a" * 100, "U1"), ("b" * 100, "U2"), ("c" * 100, "U3")]
    # Лимит такой, что помещается только часть сообщений
    text, count = format_messages_for_llm(messages, max_chars=150)
    assert count <= 2
    assert len(text) <= 150 + 50  # допуск на формат


def test_format_messages_for_llm_empty() -> None:
    """Пустой список даёт пустую строку и 0."""
    text, count = format_messages_for_llm([])
    assert text == ""
    assert count == 0


def test_format_messages_for_llm_text_truncated_to_500() -> None:
    """Текст одного сообщения обрезается до 500 символов."""
    long_text = "x" * 600
    messages = [(long_text, "User")]
    text, count = format_messages_for_llm(messages)
    assert count == 1
    assert "x" * 500 in text
    assert len(text) < 600
