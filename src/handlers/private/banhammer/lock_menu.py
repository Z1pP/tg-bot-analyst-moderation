import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import KbCommands, Dialog
from keyboards.inline.banhammer import block_actions_ikb
from states import BanHammerStates
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
        new_state=BanHammerStates.block_menu,
    )

    await message.reply(
        text=Dialog.BlockMenu.SELECT_ACTION,
        reply_markup=block_actions_ikb(),
    )
