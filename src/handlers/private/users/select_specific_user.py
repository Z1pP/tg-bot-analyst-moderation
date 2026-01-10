import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.time_period import time_period_ikb_single_user
from keyboards.inline.users import user_actions_ikb
from states.user import SingleUserReportStates
from usecases.chat_tracking import GetUserTrackedChatsUseCase
from utils.exception_handler import handle_exception
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith(CallbackData.User.PREFIX_USER))
async def user_selected_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик выбора пользователя из списка.
    """
    try:
        user_id_str = callback.data.replace(CallbackData.User.PREFIX_USER, "")
        if not user_id_str.isdigit():
            logger.error("Некорректный ID пользователя в callback: %s", callback.data)
            return

        user_id = int(user_id_str)

        await state.set_state(SingleUserReportStates.selected_single_user)
        await state.update_data(user_id=user_id)

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
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
async def get_user_report_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
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
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=Dialog.User.ERROR_SELECT_USER_AGAIN,
            )
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
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=Dialog.Report.NO_TRACKED_CHATS_FOR_REPORT,
            )
            logger.warning(
                "Админ %s пытается получить отчет без отслеживаемых чатов",
                callback.from_user.username,
            )
            return

        await state.set_state(SingleUserReportStates.selecting_period)

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Report.SELECT_PERIOD,
            reply_markup=time_period_ikb_single_user(),
        )
    except Exception as e:
        await handle_exception(callback.message, e, "get_user_report_handler")
