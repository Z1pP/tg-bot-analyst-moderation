import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from container import container
from keyboards.inline.time_period import time_period_ikb_single_user
from keyboards.inline.users import user_actions_ikb
from states.user import SingleUserReportStates
from usecases.chat_tracking import GetUserTrackedChatsUseCase
from utils.exception_handler import handle_exception
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith(CallbackData.User.PREFIX_USER))
async def user_selected_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик выбора пользователя из списка.
    """
    try:
        user_id = int(callback.data.replace(CallbackData.User.PREFIX_USER, ""))

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=SingleUserReportStates.selected_single_user,
        )
        await state.update_data(user_id=user_id)

        await callback.message.edit_text(
            text=Dialog.Report.SELECT_ACTION,
            reply_markup=user_actions_ikb(),
        )

        await callback.answer()

    except Exception as e:
        await handle_exception(
            message=callback.message, exc=e, context="user_selected_handler"
        )


@router.callback_query(
    F.data == CallbackData.Report.GET_USER_REPORT,
    SingleUserReportStates.selected_single_user,
)
async def get_user_report_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик запроса на создание отчета о времени ответа через callback."""
    try:
        await callback.answer()
        data = await state.get_data()
        user_id = data.get("user_id")

        if not user_id:
            logger.warning(
                "Отсутствует user_id в state для пользователя %s",
                callback.from_user.username,
            )
            await callback.message.edit_text(Dialog.User.ERROR_SELECT_USER_AGAIN)
            return

        logger.info(
            "Пользователь %s запросил отчет по user_id %s",
            callback.from_user.username,
            user_id,
        )

        # Проверяем наличие отслеживаемых чатов
        tracked_chats_usecase: GetUserTrackedChatsUseCase = container.resolve(
            GetUserTrackedChatsUseCase
        )
        user_chats_dto = await tracked_chats_usecase.execute(
            tg_id=str(callback.from_user.id)
        )

        if not user_chats_dto.chats:
            await callback.message.edit_text(Dialog.Report.NO_TRACKED_CHATS_FOR_REPORT)
            logger.warning(
                "Админ %s пытается получить отчет без отслеживаемых чатов",
                callback.from_user.username,
            )
            return

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=SingleUserReportStates.selecting_period,
        )

        await callback.message.edit_text(
            text=Dialog.Report.SELECT_PERIOD,
            reply_markup=time_period_ikb_single_user(),
        )
    except Exception as e:
        await handle_exception(callback.message, e, "get_user_report_handler")
