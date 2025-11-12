from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.inline.templates import templates_menu_ikb
from states import TemplateStateManager
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)


@router.callback_query(F.data == "cancel_category")
async def cancel_category_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="❌ Действие отменено.",
        reply_markup=templates_menu_ikb(),
    )
    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=TemplateStateManager.templates_menu,
    )
