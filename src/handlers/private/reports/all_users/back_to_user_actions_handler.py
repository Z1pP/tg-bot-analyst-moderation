import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.users import all_users_actions_ikb
from states import AllUsersReportStates
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == CallbackData.Report.BACK_TO_ALL_USERS_ACTIONS,
    AllUsersReportStates.selecting_period,
)
async def back_to_all_users_actions_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик возврата к действиям со всеми пользователями из выбора периода."""
    await callback.answer()

    await state.update_data(all_users_report_dto=None)

    logger.info(
        "Пользователь %s возвращается к действиям со всеми пользователями",
        callback.from_user.id,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Report.SELECT_ACTION_COLON,
        reply_markup=all_users_actions_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=AllUsersReportStates.selected_all_users,
    )
