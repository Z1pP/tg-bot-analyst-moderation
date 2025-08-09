import logging

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State

logger = logging.getLogger(__name__)


async def log_and_set_state(
    message: types.Message,
    state: FSMContext,
    new_state: State,
):
    """Логирование старого состояния и установка нового."""
    old_state = await state.get_state()
    await state.set_state(new_state)
    logger.info(
        f"[STATE] Пользователь {message.from_user.id} ({message.from_user.first_name}) "
        f"вызвал '{message.text}'. "
        f"Состояние изменено: {old_state or 'None'} -> {new_state.state}"
    )
