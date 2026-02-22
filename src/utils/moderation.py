"""Модуль вспомогательных инструментов для работы с данными пользователей."""

from dataclasses import dataclass
from typing import Optional

from aiogram.fsm.context import FSMContext


def format_violator_display(username: Optional[str], tg_id: str) -> str:
    """Возвращает строку для отображения нарушителя: @username или ID:tg_id.

    Не выводит «@» для пустого или служебного значения «hidden».
    """
    if username and username != "hidden":
        return f"@{username}"
    return f"ID:{tg_id}"


def format_violator_mention_suffix(username: Optional[str], tg_id: str) -> str:
    """Возвращает подставляемую часть для шаблона «@{username}»: username или ID:tg_id.

    Используется в диалогах вида «для @{username}», чтобы не подставлять «hidden».
    """
    if username and username != "hidden":
        return username
    return f"ID:{tg_id}"


@dataclass(frozen=True, slots=True)
class ViolatorData:
    """Данные о нарушителе, извлеченные из состояния."""

    id: int
    username: Optional[str]
    tg_id: int


async def extract_violator_data_from_state(state: FSMContext) -> ViolatorData:
    """Извлекает данные нарушителя из FSMContext.

    Args:
        state: Контекст состояния FSM.

    Returns:
        ViolatorData: Объект с данными нарушителя.
    """
    data = await state.get_data()
    return ViolatorData(
        id=data.get("id"),
        username=data.get("username"),
        tg_id=data.get("tg_id"),
    )
