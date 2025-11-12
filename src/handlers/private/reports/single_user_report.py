import logging
from datetime import datetime
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from constants.period import TimePeriod
from container import container
from dto.report import SingleUserReportDTO
from keyboards.inline import CalendarKeyboard, order_details_kb
from keyboards.reply import get_time_period_kb
from services.time_service import TimeZoneService
from services.work_time_service import WorkTimeService
from states import SingleUserReportStates
from usecases.chat_tracking import GetUserTrackedChatsUseCase
from usecases.report import GetSingleUserReportUseCase

from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(
    F.text == KbCommands.GET_REPORT,
    SingleUserReportStates.selected_single_user,
)
async def single_user_report_handler(message: Message, state: FSMContext) -> None:
    """Обработчик запроса на создание отчета о времени ответа."""
    try:
        data = await state.get_data()
        user_id = data.get("user_id")

        if not user_id:
            logger.warning(
                "Отсутствует user_id в state для пользователя %s",
                message.from_user.username,
            )
            await message.answer("❌ Ошибка: выберите пользователя заново")
            return

        logger.info(
            "Пользователь %s запросил отчет по user_id %s",
            message.from_user.username,
            user_id,
        )

        # Проверяем наличие отслеживаемых чатов
        tracked_chats_usecase: GetUserTrackedChatsUseCase = container.resolve(
            GetUserTrackedChatsUseCase
        )
        user_chats_dto = await tracked_chats_usecase.execute(
            tg_id=str(message.from_user.id)
        )

        if not user_chats_dto.chats:
            await message.answer(
                "❌ У вас нет отслеживаемых чатов.\n"
                "Добавьте чаты в отслеживание для составления отчета."
            )
            logger.warning(
                "Админ %s пытается получить отчет без отслеживаемых чатов",
                message.from_user.username,
            )
            return

        await log_and_set_state(
            message=message,
            state=state,
            new_state=SingleUserReportStates.selecting_period,
        )

        await send_html_message_with_kb(
            message=message,
            text="Выберите период для отчета",
            reply_markup=get_time_period_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "single_user_report_handler")


@router.message(
    SingleUserReportStates.selecting_period,
    F.text.in_(TimePeriod.get_all_periods()),
)
async def process_period_selection(message: Message, state: FSMContext) -> None:
    """Обрабатывает выбор периода для отчета о времени ответа."""
    try:
        user_data = await state.get_data()
        user_id = user_data.get("user_id")

        logger.info(
            "Выбран период для user_id %s: %s",
            user_id,
            message.text,
        )

        if not user_id:
            logger.warning("Отсутствует user_id при выборе периода")
            await message.answer("❌ Ошибка: выберите пользователя заново")
            return

        if message.text == TimePeriod.CUSTOM.value:
            await log_and_set_state(
                message=message,
                state=state,
                new_state=SingleUserReportStates.selecting_custom_period,
            )

            # Показываем календарь
            now = TimeZoneService.now()
            await state.update_data(cal_start_date=None, cal_end_date=None)

            calendar_kb = CalendarKeyboard.create_calendar(
                year=now.year,
                month=now.month,
            )

            await message.answer(
                text="📅 Выберите начальную дату диапазона:",
                reply_markup=calendar_kb,
            )
            return

        start_date, end_date = TimePeriod.to_datetime(period=message.text)
        logger.info(
            "Генерация отчета по user_id %s за период: %s - %s",
            user_id,
            start_date,
            end_date,
        )

        await generate_and_send_report(
            message=message,
            state=state,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            selected_period=message.text,
        )
    except Exception as e:
        await handle_exception(message, e, "process_period_selection")


async def generate_and_send_report(
    message: Message,
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
            admin_tg_id=str(admin_tg_id or message.from_user.id),
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
            message=message,
            state=state,
            new_state=SingleUserReportStates.selecting_period,
        )

        for idx, part in enumerate(report_parts):
            if idx == len(report_parts) - 1:
                part = f"{part}\n\nДля продолжения выберите период, либо нажмите назад"

            await send_html_message_with_kb(
                message=message,
                text=part,
                reply_markup=order_details_kb(show_details=not is_single_day),
            )

        logger.info("Отчет по user_id %s успешно отправлен", user_id)
    except Exception as e:
        logger.error(
            "Ошибка при генерации/отправке отчета по user_id %s: %s",
            user_id,
            e,
            exc_info=True,
        )
        await handle_exception(message, e, "generate_and_send_report")
