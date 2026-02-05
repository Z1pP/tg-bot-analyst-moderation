"""Модуль вспомогательных инструментов для работы с данными пользователей."""

from dataclasses import dataclass

from aiogram.fsm.context import FSMContext


@dataclass(frozen=True, slots=True)
class ViolatorData:
    """Данные о нарушителе, извлеченные из состояния."""

    id: int
    username: str
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
