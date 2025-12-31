import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.time_period import time_period_ikb_single_user
from states import SingleUserReportStates
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == CallbackData.Report.BACK_TO_PERIODS,
    SingleUserReportStates.selecting_period,
)
@router.callback_query(
    F.data == CallbackData.Report.BACK_TO_PERIODS,
    SingleUserReportStates.selecting_custom_period,
)
async def back_to_periods_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик возврата к выбору периода отчета для одного пользователя."""
    await callback.answer()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Report.SELECT_PERIOD,
        reply_markup=time_period_ikb_single_user(),
    )

    await state.set_state(SingleUserReportStates.selecting_period)
