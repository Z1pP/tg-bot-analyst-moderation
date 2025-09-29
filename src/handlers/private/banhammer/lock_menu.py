import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import KbCommands
from states import LockStates
from utils.state_logger import log_and_set_state

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(F.text == KbCommands.LOCK_MENU)
async def lock_menu_handler(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик отвечающий за вывод настроек блокировки.
    """
    await log_and_set_state(
        message=message,
        state=state,
        new_state=LockStates.lock_menu,
    )

    await message.answer(f"Вкладка {KbCommands.LOCK_MENU} еще в разработке!")
