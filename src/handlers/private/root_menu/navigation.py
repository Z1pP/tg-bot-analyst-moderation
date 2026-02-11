from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.root import root_menu_ikb
from utils.send_message import safe_edit_message

router = Router(name="root_navigation_router")


@router.callback_query(F.data == CallbackData.Root.SHOW_MENU)
async def root_menu_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Root.MENU_TEXT,
        reply_markup=root_menu_ikb(),
    )
