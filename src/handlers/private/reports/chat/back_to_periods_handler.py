import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from keyboards.inline.time_period import time_period_ikb_chat
from states import ChatStateManager

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == "back_to_periods",
    ChatStateManager.selecting_period,
)
@router.callback_query(
    F.data == "back_to_periods",
    ChatStateManager.selecting_custom_period,
)
async def back_to_periods_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик возврата к выбору периода отчета для чата."""
    await callback.answer()

    logger.info(
        "Пользователь %s возвращается к выбору периода",
        callback.from_user.id,
    )

    await callback.message.edit_text(
        text=Dialog.Report.SELECT_PERIOD,
        reply_markup=time_period_ikb_chat(),
    )
