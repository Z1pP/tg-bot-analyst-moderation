import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.users import user_actions_ikb
from states import SingleUserReportStates
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == CallbackData.Report.BACK_TO_SINGLE_USER_ACTIONS,
    SingleUserReportStates.selecting_period,
)
async def back_to_single_user_actions_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик возврата к действиям с пользователем из выбора периода."""
    await callback.answer()

    await state.update_data(report_dto=None)

    logger.info(
        "Пользователь %s возвращается к действиям с пользователем",
        callback.from_user.id,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Report.SELECT_ACTION,
        reply_markup=user_actions_ikb(),
    )

    await state.set_state(SingleUserReportStates.selected_single_user)
