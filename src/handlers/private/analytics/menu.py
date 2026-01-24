from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline import analytics_menu_ikb
from utils.send_message import safe_edit_message

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.Analytics.SHOW_MENU)
async def analytics_menu_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Analytics.MENU_INFO,
        reply_markup=analytics_menu_ikb(),
    )
