import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.time_period import time_period_ikb_chat
from states import ChatStateManager, RatingStateManager
from utils.send_message import safe_edit_message

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == CallbackData.Report.BACK_TO_PERIODS,
    ChatStateManager.selecting_period,
)
@router.callback_query(
    F.data == CallbackData.Report.BACK_TO_PERIODS,
    ChatStateManager.selecting_custom_period,
)
@router.callback_query(
    F.data == CallbackData.Report.BACK_TO_PERIODS,
    RatingStateManager.selecting_period,
)
@router.callback_query(
    F.data == CallbackData.Report.BACK_TO_PERIODS,
    RatingStateManager.selecting_custom_period,
)
async def back_to_periods_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик возврата к выбору периода отчета для чата."""
    await callback.answer()

    current_state = await state.get_state()
    logger.info(
        "Пользователь %s возвращается к выбору периода из состояния %s",
        callback.from_user.id,
        current_state,
    )

    # Определяем текст и новое состояние в зависимости от текущего состояния
    if current_state and "RatingStateManager" in current_state:
        text = Dialog.Rating.SELECT_PERIOD
        new_state = RatingStateManager.selecting_period
    else:
        text = Dialog.Report.SELECT_PERIOD
        new_state = ChatStateManager.selecting_period

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=time_period_ikb_chat(),
    )

    await state.set_state(new_state)
