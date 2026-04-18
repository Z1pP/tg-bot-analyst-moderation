"""Тесты разбора карточки автомодерации."""

from constants import Dialog
from utils.parse_automoderation_card import parse_automoderation_card


def test_parse_full_plain_and_html_link() -> None:
    """Причина и id сообщения из текста и ссылки в HTML."""
    text = (
        "Нарушитель: @spammer\n"
        "ID: 123\n"
        "Причина: реклама\n"
        "Чат: My chat\n"
        "Сообщение: ссылка"
    )
    html = text.replace(
        "Сообщение: ссылка",
        'Сообщение: <a href="https://t.me/c/1234567890/42">ссылка</a>',
    )
    r = parse_automoderation_card(text=text, html_text=html)
    assert r.reason == "реклама"
    assert r.reply_message_id == 42
    assert r.violator_username_hint == "spammer"


def test_parse_skips_no_username_label() -> None:
    """Подсказка username не заполняется для плейсхолдера «Отсутствует»."""
    text = (
        f"Нарушитель: {Dialog.AutoModeration.NO_USERNAME}\n"
        'Сообщение: <a href="https://t.me/c/1/99">x</a>'
    )
    r = parse_automoderation_card(text=text, html_text=text)
    assert r.violator_username_hint is None
    assert r.reply_message_id == 99


def test_parse_link_from_plain_only() -> None:
    """Ссылка без HTML (редко, но допустимо)."""
    text = "Причина: x\nhttps://t.me/c/555/7"
    r = parse_automoderation_card(text=text)
    assert r.reply_message_id == 7
    assert r.reason == "x"
