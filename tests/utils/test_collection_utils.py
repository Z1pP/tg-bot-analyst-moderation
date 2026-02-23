"""Тесты для utils/collection_utils.py."""

from utils.collection_utils import group_by


def test_group_by_empty() -> None:
    """Пустой итератор даёт пустой словарь."""
    assert group_by([], key=lambda x: x) == {}


def test_group_by_single_group() -> None:
    """Один ключ — одна группа."""
    items = [1, 2, 3]
    result = group_by(items, key=lambda x: "same")
    assert result == {"same": [1, 2, 3]}


def test_group_by_multiple_groups() -> None:
    """Несколько ключей — несколько групп."""
    items = [1, 2, 3, 4]
    result = group_by(items, key=lambda x: x % 2)
    assert result == {0: [2, 4], 1: [1, 3]}


def test_group_by_dict_items() -> None:
    """Группировка по ключу элемента (например, по первой букве)."""
    items = ["apple", "banana", "apricot"]
    result = group_by(items, key=lambda s: s[0])
    assert result == {"a": ["apple", "apricot"], "b": ["banana"]}
