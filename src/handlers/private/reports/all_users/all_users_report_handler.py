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
from dto.report import AllUsersReportDTO
from keyboards.inline import CalendarKeyboard, all_users_actions_ikb
from keyboards.inline.report import order_details_kb_all_users
from keyboards.inline.time_period import time_period_ikb_all_users
from presenters import AllUsersReportPresenter
from services.time_service import TimeZoneService
from states import AllUsersReportStates
from usecases.chat_tracking import GetUserTrackedChatsUseCase
from usecases.report import GetAllUsersReportUseCase
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == CallbackData.Report.GET_ALL_USERS_REPORT,
    AllUsersReportStates.selected_all_users,
)
async def get_all_users_report_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик запроса на создание отчета по всем пользователям"""
    await callback.answer()

    logger.info(
        "Пользователь %s запросил отчет по всем пользователям",
        callback.from_user.id,
    )
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
            reply_markup=all_users_actions_ikb(),
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
            reply_markup=all_users_actions_ikb(),
        )
        return

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Report.SELECT_PERIOD_COLON,
        reply_markup=time_period_ikb_all_users(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=AllUsersReportStates.selecting_period,
    )


@router.callback_query(
    AllUsersReportStates.selecting_period,
    F.data.startswith(CallbackData.Report.PREFIX_PERIOD),
)
async def process_period_selection_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обрабатывает выбор периода для отчета через callback."""
    await callback.answer()

    period_text = callback.data.replace(CallbackData.Report.PREFIX_PERIOD, "")
    logger.info("Выбран период: %s", period_text)

    if period_text == TimePeriod.CUSTOM.value:
        logger.info("Запрос пользовательского периода")

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=AllUsersReportStates.selecting_custom_period,
        )

        # Показываем календарь
        now = TimeZoneService.now()
        await state.update_data(cal_start_date=None, cal_end_date=None)

        calendar_kb = CalendarKeyboard.create_calendar_all_users(
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

    start_date, end_date = TimePeriod.to_datetime(period_text)

    try:
        await _render_all_users_report(
            callback=callback,
            state=state,
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
            reply_markup=all_users_actions_ikb(),
        )
        return


async def _render_all_users_report(
    callback: CallbackQuery,
    state: FSMContext,
    start_date: datetime,
    end_date: datetime,
    selected_period: str | None = None,
) -> None:
    """
    Presentation Layer: форматирует и отправляет отчет пользователю.
    Управляет FSM состоянием и клавиатурами.

    Args:
        callback: Callback query
        state: FSM context
        start_date: Начальная дата
        end_date: Конечная дата
        selected_period: Текстовый период (например, "today", "yesterday")
    """
    try:
        logger.info(
            "Начало генерации отчета за период %s - %s",
            start_date,
            end_date,
        )

        report_dto = AllUsersReportDTO(
            user_tg_id=str(callback.from_user.id),
            start_date=start_date,
            end_date=end_date,
            selected_period=selected_period,
        )

        usecase: GetAllUsersReportUseCase = container.resolve(GetAllUsersReportUseCase)
        result = await usecase.execute(report_dto)

        logger.info("Отчет сгенерирован")

        # Форматируем результат через Presenter
        presenter = AllUsersReportPresenter()
        report_parts = presenter.format_report(result)

        if result.error_message:
            # Если есть ошибка, presenter уже вернул её в report_parts
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=report_parts[0] if report_parts else result.error_message,
                reply_markup=all_users_actions_ikb(),
            )
            return

        # Сохраняем report_dto для детализации (только для многодневных отчетов)
        if not result.is_single_day:
            await state.update_data(all_users_report_dto=report_dto)

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=AllUsersReportStates.selecting_period,
        )

        # Объединяем все части отчета в один текст
        full_report = "\n\n".join(report_parts)

        await callback.message.edit_text(
            text=full_report,
            parse_mode=ParseMode.HTML,
            reply_markup=order_details_kb_all_users(
                show_details=not result.is_single_day,
            ),
        )

        logger.info("Отчет успешно отправлен пользователю")
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
            reply_markup=all_users_actions_ikb(),
        )
