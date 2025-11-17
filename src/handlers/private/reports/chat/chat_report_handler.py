import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.period import TimePeriod
from container import container
from dto.report import ChatReportDTO
from keyboards.inline import CalendarKeyboard
from keyboards.inline.chats_kb import chat_actions_ikb
from keyboards.inline.report import order_details_kb_chat
from keyboards.inline.time_period import time_period_ikb_chat
from services.time_service import TimeZoneService
from services.work_time_service import WorkTimeService
from states import ChatStateManager
from usecases.report import GetReportOnSpecificChatUseCase
from usecases.user_tracking import GetListTrackedUsersUseCase
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == "get_chat_report",
    ChatStateManager.selecting_chat,
)
async def chat_report_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик запроса на создание отчета по конкретному чату."""
    await callback.answer()

    try:
        tracked_users_usecase: GetListTrackedUsersUseCase = container.resolve(
            GetListTrackedUsersUseCase
        )
        tracked_users = await tracked_users_usecase.execute(
            admin_tgid=str(callback.from_user.id)
        )
    except Exception as e:
        logger.error(
            "Ошибка при получении списка отслеживаемых пользователей: %s",
            e,
            exc_info=True,
        )
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Report.ERROR_GET_TRACKED_USERS,
            reply_markup=chat_actions_ikb(),
        )
        return

    if not tracked_users:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Report.NO_TRACKED_USERS,
            reply_markup=chat_actions_ikb(),
        )
        logger.warning(
            "Админ %s пытается получить отчет без отслеживаемых пользователей",
            callback.from_user.username,
        )
        return

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Report.SELECT_PERIOD,
        reply_markup=time_period_ikb_chat(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=ChatStateManager.selecting_period,
    )


@router.callback_query(
    ChatStateManager.selecting_period,
    F.data.startswith("period__"),
)
async def process_period_selection_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обрабатывает выбор периода для отчета по чату через callback."""
    await callback.answer()

    period_text = callback.data.replace("period__", "")
    data = await state.get_data()
    chat_id = data.get("chat_id")

    logger.info(
        "Пользователь %s выбрал период %s для чата %s",
        callback.from_user.username,
        chat_id,
        period_text,
    )

    if period_text == TimePeriod.CUSTOM.value:
        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=ChatStateManager.selecting_custom_period,
        )

        # Показываем календарь
        now = TimeZoneService.now()
        await state.update_data(cal_start_date=None, cal_end_date=None)

        calendar_kb = CalendarKeyboard.create_calendar_chat(
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
        "Генерация отчета по чату %s за период: %s - %s",
        chat_id,
        start_date,
        end_date,
    )

    await generate_and_send_report(
        callback,
        state,
        start_date,
        end_date,
        chat_id,
        selected_period=period_text,
    )


async def select_chat_again(callback: CallbackQuery, state: FSMContext) -> None:
    """Повторно запрашивает выбор чата."""
    logger.info("Запрос повторного выбора чата")

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=ChatStateManager.selecting_chat,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Report.SELECT_CHAT_AGAIN,
        reply_markup=chat_actions_ikb(),
    )


async def generate_and_send_report(
    callback: CallbackQuery,
    state: FSMContext,
    start_date: datetime,
    end_date: datetime,
    chat_id: int,
    selected_period: str | None = None,
    admin_tg_id: int | None = None,
) -> None:
    """Генерирует и отправляет отчет по чату."""

    user_id = admin_tg_id or callback.from_user.id

    logger.info(
        "Начало генерации отчета по чату %s за период %s - %s",
        chat_id,
        start_date,
        end_date,
    )

    adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
        start_date, end_date
    )

    report_dto = ChatReportDTO(
        chat_id=chat_id,
        admin_tg_id=str(user_id),
        start_date=adjusted_start,
        end_date=adjusted_end,
        selected_period=selected_period,
    )

    try:
        usecase: GetReportOnSpecificChatUseCase = container.resolve(
            GetReportOnSpecificChatUseCase
        )
        is_single_day = usecase.is_single_day_report(report_dto)
        report_parts = await usecase.execute(dto=report_dto)
    except Exception as e:
        logger.error(
            "Ошибка при генерации отчета по чату %s: %s",
            chat_id,
            e,
            exc_info=True,
        )
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Report.ERROR_GENERATING_REPORT,
            reply_markup=chat_actions_ikb(),
        )
        return

    logger.info(
        "Отчет по чату %s сгенерирован, частей: %s",
        chat_id,
        len(report_parts),
    )

    # Сохраняем report_dto для детализации (только для многодневных отчетов)
    if not is_single_day:
        await state.update_data(chat_report_dto=report_dto)

    # Объединяем все части отчета в один текст
    full_report = "\n\n".join(report_parts)
    if not is_single_day:
        full_report = f"{full_report}{Dialog.Report.CONTINUE_SELECT_PERIOD}"

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=full_report,
        parse_mode=ParseMode.HTML,
        reply_markup=order_details_kb_chat(show_details=not is_single_day),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=ChatStateManager.selecting_period,
    )
