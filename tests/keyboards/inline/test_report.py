"""Тесты клавиатур отчётов (keyboards/inline/report.py)."""

from aiogram.types import InlineKeyboardMarkup

from keyboards.inline.report import (
    hide_details_ikb,
    order_details_kb_all_users,
    order_details_kb_chat,
    order_details_kb_single_user,
)


def test_order_details_kb_single_user_returns_markup() -> None:
    """order_details_kb_single_user возвращает InlineKeyboardMarkup."""
    kb = order_details_kb_single_user(show_details=True)
    assert isinstance(kb, InlineKeyboardMarkup)
    assert kb.inline_keyboard is not None


def test_order_details_kb_single_user_hide_details() -> None:
    """order_details_kb_single_user с show_details=False не падает."""
    kb = order_details_kb_single_user(show_details=False)
    assert isinstance(kb, InlineKeyboardMarkup)


def test_order_details_kb_all_users_returns_markup() -> None:
    """order_details_kb_all_users возвращает InlineKeyboardMarkup."""
    kb = order_details_kb_all_users(show_details=True)
    assert isinstance(kb, InlineKeyboardMarkup)


def test_order_details_kb_chat_returns_markup() -> None:
    """order_details_kb_chat возвращает InlineKeyboardMarkup с минимальными аргументами."""
    kb = order_details_kb_chat()
    assert isinstance(kb, InlineKeyboardMarkup)


def test_hide_details_ikb_returns_markup() -> None:
    """hide_details_ikb с списком message_ids возвращает InlineKeyboardMarkup."""
    kb = hide_details_ikb(message_ids=[1, 2, 3])
    assert isinstance(kb, InlineKeyboardMarkup)
    assert len(kb.inline_keyboard) >= 1


def test_hide_details_ikb_empty_list() -> None:
    """hide_details_ikb с пустым списком не падает."""
    kb = hide_details_ikb(message_ids=[])
    assert isinstance(kb, InlineKeyboardMarkup)
