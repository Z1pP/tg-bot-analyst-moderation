from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog, InlineButtons
from keyboards.inline.banhammer import block_actions_ikb
from states.banhammer_states import BanHammerStates
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
block_buttons = InlineButtons.BlockButtons()


@router.callback_query(F.data == block_buttons.BACK_TO_BLOCK_MENU)
async def back_to_block_menu_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик для возврата в меню блокировок"""

    await callback.answer()

    await callback.message.edit_text(
        text=Dialog.BlockMenu.SELECT_ACTION,
        reply_markup=block_actions_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=BanHammerStates.block_menu,
    )
