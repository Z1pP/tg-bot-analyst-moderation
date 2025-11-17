import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import Dialog, KbCommands
from constants.period import TimePeriod
from container import container
from dto.report import ChatReportDTO
from keyboards.inline import CalendarKeyboard
from keyboards.inline.report import order_details_kb_chat
from keyboards.reply import admin_menu_kb, chat_actions_kb, get_time_period_kb
from services.time_service import TimeZoneService
from services.work_time_service import WorkTimeService
from states import ChatStateManager
from usecases.report import GetReportOnSpecificChatUseCase
from usecases.user_tracking import GetListTrackedUsersUseCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(
    ChatStateManager.selecting_chat,
    F.text == KbCommands.GET_REPORT,
)
async def chat_report_handler(message: Message, state: FSMContext) -> None:
    """Обработчик запроса на создание отчета по конкретному чату."""
    try:
        data = await state.get_data()
        chat_id = data.get("chat_id")

        if not chat_id:
            await select_chat_again(message=message, state=state)
            return
        logger.info(
            "Пользователь %s запросил отчет по чату %s",
            message.from_user.username,
            chat_id,
        )

        tracked_users_usecase: GetListTrackedUsersUseCase = container.resolve(
            GetListTrackedUsersUseCase
        )
        tracked_users = await tracked_users_usecase.execute(
            admin_tgid=str(message.from_user.id)
        )

        if not tracked_users:
            await message.answer(
                Dialog.Report.NO_TRACKED_USERS,
                reply_markup=chat_actions_kb(),
            )
            logger.warning(
                "Админ %s пытается получить отчет без отслеживаемых пользователей",
                message.from_user.username,
            )
            return

        await log_and_set_state(
            message=message,
            state=state,
            new_state=ChatStateManager.selecting_period,
        )

        await send_html_message_with_kb(
            text=Dialog.Report.SELECT_PERIOD,
            message=message,
            reply_markup=get_time_period_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "specific_chat_report")


@router.message(
    ChatStateManager.selecting_period,
    F.text.in_(TimePeriod.get_all_periods()),
)
async def process_report_input(message: Message, state: FSMContext) -> None:
    """Обрабатывает выбор периода для отчета."""
    try:
        data = await state.get_data()
        chat_id = data.get("chat_id")

        logger.info(
            "Выбран период для чата %s: %s",
            chat_id,
            message.text,
        )

        if not chat_id:
            logger.warning("Отсутствует название чата при выборе периода")
            await select_chat_again(message=message, state=state)
            return

        if message.text == TimePeriod.CUSTOM.value:
            await log_and_set_state(
                message=message,
                state=state,
                new_state=ChatStateManager.selecting_custom_period,
            )

            # Показываем календарь
            now = TimeZoneService.now()
            await state.update_data(cal_start_date=None, cal_end_date=None)

            calendar_kb = CalendarKeyboard.create_calendar(
                year=now.year,
                month=now.month,
            )

            await message.answer(
                text=Dialog.Report.SELECT_START_DATE,
                reply_markup=calendar_kb,
            )
            return

        start_date, end_date = TimePeriod.to_datetime(message.text)
        logger.info(
            "Генерация отчета по чату %s за период: %s - %s",
            chat_id,
            start_date,
            end_date,
        )

        await generate_and_send_report(
            message=message,
            state=state,
            start_date=start_date,
            end_date=end_date,
            chat_id=chat_id,
            selected_period=message.text,
        )
    except Exception as e:
        await handle_exception(message, e, "process_report_input")


async def select_chat_again(message: Message, state: FSMContext) -> None:
    """Повторно запрашивает выбор чата."""

    logger.info("Запрос повторного выбора чата")
    await log_and_set_state(
        message=message,
        state=state,
        new_state=ChatStateManager.selecting_chat,
    )
    await send_html_message_with_kb(
        message=message,
        text=Dialog.Report.SELECT_CHAT_AGAIN,
        reply_markup=admin_menu_kb(),
    )


async def generate_and_send_report(
    message: Message,
    state: FSMContext,
    start_date: datetime,
    end_date: datetime,
    chat_id: int,
    selected_period: str | None = None,
    admin_tg_id: int | None = None,
) -> None:
    """Генерирует и отправляет отчет по чату."""
    try:
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
            admin_tg_id=str(admin_tg_id or message.from_user.id),
            start_date=adjusted_start,
            end_date=adjusted_end,
            selected_period=selected_period,
        )

        usecase: GetReportOnSpecificChatUseCase = container.resolve(
            GetReportOnSpecificChatUseCase
        )
        is_single_day = usecase.is_single_day_report(report_dto)
        report_parts = await usecase.execute(dto=report_dto)

        logger.info(
            "Отчет по чату %s сгенерирован, частей: %s",
            chat_id,
            len(report_parts),
        )

        # Сохраняем report_dto для детализации (только для многодневных отчетов)
        if not is_single_day:
            await state.update_data(chat_report_dto=report_dto)

        await log_and_set_state(
            message=message,
            state=state,
            new_state=ChatStateManager.selecting_period,
        )

        for idx, part in enumerate(report_parts):
            if idx == len(report_parts) - 1:
                part = f"{part}{Dialog.Report.CONTINUE_SELECT_PERIOD}"

            await send_html_message_with_kb(
                message=message,
                text=part,
                reply_markup=order_details_kb_chat(show_details=not is_single_day),
            )

        logger.info("Отчет по чату %s успешно отправлен", chat_id)
    except Exception as e:
        logger.error(
            "Ошибка при генерации/отправке отчета по чату %s: %s",
            chat_id,
            e,
            exc_info=True,
        )
        await handle_exception(message, e, "generate_and_send_report")
