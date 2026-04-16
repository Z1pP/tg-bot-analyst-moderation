"""Утилиты выбора чатов из списка по данным callback (chat__all / chat__<id>)."""

from collections.abc import Iterable

from dto.chat_dto import ChatDTO


def filter_chats_by_callback_selection(
    chats: Iterable[ChatDTO],
    selection: str,
) -> list[ChatDTO]:
    """Возвращает все чаты или один с указанным внутренним id (БД).

    Args:
        chats: Чаты из state (после model_validate).
        selection: Вторая часть callback после разбиения по '__': ``all`` или строка с int id.
    """
    if selection == "all":
        return list(chats)
    chat_id = int(selection)
    return [chat for chat in chats if chat.id == chat_id]
