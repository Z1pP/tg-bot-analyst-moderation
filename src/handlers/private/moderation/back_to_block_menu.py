from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog, InlineButtons
from keyboards.inline.moderation import moderation_menu_ikb
from states.moderation import ModerationStates
from utils.send_message import safe_edit_message

router = Router(name=__name__)
block_buttons = InlineButtons.BlockButtons()


@router.callback_query(F.data == block_buttons.BACK_TO_BLOCK_MENU)
async def back_to_block_menu_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик для возврата в меню блокировок"""

    await callback.answer()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Moderation.SELECT_ACTION,
        reply_markup=moderation_menu_ikb(),
    )

    await state.set_state(ModerationStates.menu)
