import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from constants.period import TimePeriod
from container import container
from dto.report import SingleUserReportDTO
from keyboards.inline import CalendarKeyboard, user_actions_ikb
from keyboards.inline.report import order_details_kb_single_user
from keyboards.inline.time_period import time_period_ikb_single_user
from services.time_service import TimeZoneService
from services.work_time_service import WorkTimeService
from states import SingleUserReportStates
from usecases.chat_tracking import GetUserTrackedChatsUseCase
from usecases.report import GetSingleUserReportUseCase
from utils.exception_handler import handle_exception
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == CallbackData.Report.GET_USER_REPORT,
    SingleUserReportStates.selected_single_user,
)
async def get_user_report_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик запроса на создание отчета через callback (возврат из периодов)."""
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
            text=Dialog.Report.ERROR_SELECT_USER_AGAIN,
            reply_markup=user_actions_ikb(),
        )
        return

    try:
        tracked_chats_usecase: GetUserTrackedChatsUseCase = container.resolve(
            GetUserTrackedChatsUseCase
        )
        user_chats_dto = await tracked_chats_usecase.execute(
            tg_id=str(callback.from_user.id)
        )
    except Exception as e:
        logger.error(
            "Ошибка при получении отчета по всем пользователям: %s",
            e,
            exc_info=True,
        )
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Report.ERROR_GETTING_TRACKED_CHATS,
            reply_markup=user_actions_ikb(),
        )

        return

    if not user_chats_dto.chats:
        logger.warning(
            "Админ %s пытается получить отчет без отслеживаемых чатов",
            callback.from_user.username,
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Report.NO_TRACKED_CHATS_WITH_INSTRUCTIONS,
            reply_markup=user_actions_ikb(),
        )
        return

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Report.SELECT_PERIOD,
        reply_markup=time_period_ikb_single_user(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=SingleUserReportStates.selecting_period,
    )


@router.callback_query(
    SingleUserReportStates.selecting_period,
    F.data.startswith(CallbackData.Report.PREFIX_PERIOD),
)
async def process_period_selection_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обрабатывает выбор периода для отчета о времени ответа через callback."""
    await callback.answer()

    period_text = callback.data.replace(CallbackData.Report.PREFIX_PERIOD, "")
    user_data = await state.get_data()
    user_id = user_data.get("user_id")

    logger.info(
        "Выбран период для user_id %s: %s",
        user_id,
        period_text,
    )

    if period_text == TimePeriod.CUSTOM.value:
        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=SingleUserReportStates.selecting_custom_period,
        )

        # Показываем календарь
        now = TimeZoneService.now()
        await state.update_data(cal_start_date=None, cal_end_date=None)

        calendar_kb = CalendarKeyboard.create_calendar_single_user(
            year=now.year,
            month=now.month,
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Report.SELECT_START_DATE,
            reply_markup=calendar_kb,
        )

        return

    start_date, end_date = TimePeriod.to_datetime(period=period_text)
    logger.info(
        "Генерация отчета по user_id %s за период: %s - %s",
        user_id,
        start_date,
        end_date,
    )
    try:
        await generate_and_send_report(
            callback=callback,
            state=state,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            selected_period=period_text,
        )
    except Exception as e:
        logger.error(
            "Ошибка при генерации/отправке отчета: %s",
            e,
            exc_info=True,
        )
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Report.ERROR_GENERATING_REPORT,
            reply_markup=user_actions_ikb(),
        )
        return


async def generate_and_send_report(
    callback: CallbackQuery,
    state: FSMContext,
    user_id: int,
    start_date: datetime,
    end_date: datetime,
    selected_period: str | None = None,
    admin_tg_id: int | None = None,
) -> None:
    """Генерирует и отправляет отчет."""
    try:
        logger.info(
            "Начало генерации отчета по user_id %s за период %s - %s",
            user_id,
            start_date,
            end_date,
        )

        adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
            start_date, end_date
        )

        report_dto = SingleUserReportDTO(
            user_id=user_id,
            admin_tg_id=str(admin_tg_id or callback.from_user.id),
            start_date=adjusted_start,
            end_date=adjusted_end,
            selected_period=selected_period,
        )

        usecase: GetSingleUserReportUseCase = container.resolve(
            GetSingleUserReportUseCase
        )
        is_single_day = usecase.is_single_day_report(report_dto)
        report_parts = await usecase.execute(report_dto=report_dto)

        logger.info(
            "Отчет по user_id %s сгенерирован, частей: %s",
            user_id,
            len(report_parts),
        )

        # Сохраняем report_dto для детализации (только для многодневных отчетов)
        if not is_single_day:
            await state.update_data(report_dto=report_dto)

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=SingleUserReportStates.selecting_period,
        )

        # Объединяем все части отчета в один текст
        full_report = "\n\n".join(report_parts)

        await callback.message.edit_text(
            text=full_report,
            parse_mode=ParseMode.HTML,
            reply_markup=order_details_kb_single_user(
                show_details=not is_single_day,
            ),
        )
        await callback.answer()

        logger.info("Отчет по user_id %s успешно отправлен", user_id)
    except Exception as e:
        logger.error(
            "Ошибка при генерации/отправке отчета по user_id %s: %s",
            user_id,
            e,
            exc_info=True,
        )
        await handle_exception(callback.message, e, "generate_and_send_report")
