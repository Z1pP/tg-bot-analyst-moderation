import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from keyboards.inline.time_period import time_period_ikb_all_users
from states import AllUsersReportStates
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == "back_to_periods",
    AllUsersReportStates.selecting_period,
)
@router.callback_query(
    F.data == "back_to_periods",
    AllUsersReportStates.selecting_custom_period,
)
async def back_to_periods_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик возврата к выбору периода отчета для всех пользователей."""
    await callback.answer()

    logger.info(
        "Пользователь %s возвращается к выбору периода",
        callback.from_user.id,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Report.SELECT_PERIOD_COLON,
        reply_markup=time_period_ikb_all_users(),
    )
