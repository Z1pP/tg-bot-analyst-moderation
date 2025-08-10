import logging
from datetime import datetime
from typing import List, Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from constants.period import TimePeriod
from container import container
from dto.report import AllUsersReportDTO
from keyboards.reply import get_time_period_for_full_report
from services.work_time_service import WorkTimeService
from states import AllUsersReportStates
from usecases.report import GetAllUsersReportUseCase
from utils.command_parser import parse_date
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(
    F.text == KbCommands.GET_STATISTICS,
    AllUsersReportStates.selected_all_users,
)
async def all_users_report_handler(message: Message, state: FSMContext) -> None:
    """Обработчик для получения отчета по всем пользователям за период."""
    try:
        logger.info(
            f"Пользователь {message.from_user.id} запросил отчет по всем пользователям"
        )

        await log_and_set_state(
            message=message,
            state=state,
            new_state=AllUsersReportStates.selecting_period,
        )

        await send_html_message_with_kb(
            message=message,
            text="Выберите период для отчета:",
            reply_markup=get_time_period_for_full_report(),
        )
    except Exception as e:
        await handle_exception(message, e, "all_users_report_handler")


@router.message(
    AllUsersReportStates.selecting_period,
    F.text.in_(TimePeriod.get_all_periods()),
)
async def process_period_selection(message: Message, state: FSMContext) -> None:
    """Обрабатывает выбор периода для отчета."""
    try:
        logger.info(f"Выбран период: {message.text}")

        if message.text == TimePeriod.CUSTOM.value:
            logger.info("Запрос пользовательского периода")
            await log_and_set_state(
                message=message,
                state=state,
                new_state=AllUsersReportStates.waiting_custom_period,
            )

            await send_html_message_with_kb(
                message=message,
                text="Введите период в формате DD.MM-DD.MM\n"
                "Например: 16.04-20.04 или 16.04- (с 16.04 до сегодня)",
            )
            return

        start_date, end_date = TimePeriod.to_datetime(message.text)
        logger.info(f"Генерация отчета за период: {start_date} - {end_date}")

        await generate_and_send_report(
            message=message,
            state=state,
            start_date=start_date,
            end_date=end_date,
            selected_period=message.text,
        )
    except Exception as e:
        await handle_exception(message, e, "process_period_selection")


@router.message(AllUsersReportStates.waiting_custom_period)
async def process_custom_period_input(message: Message, state: FSMContext) -> None:
    """Обрабатывает ввод пользовательского периода для отчета."""
    try:
        logger.info(f"Получен пользовательский период: {message.text}")

        start_date, end_date = parse_date(message.text)
        logger.info(f"Парсинг периода успешен: {start_date} - {end_date}")

        await generate_and_send_report(
            message=message,
            state=state,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as e:
        logger.warning(f"Некорректный формат даты: {message.text}, ошибка: {e}")
        await send_html_message_with_kb(
            message=message,
            text=f"❌ Некорректный формат даты: {str(e)}\n"
            "Пожалуйста, введите период в формате DD.MM-DD.MM",
            reply_markup=get_time_period_for_full_report(),
        )
    except Exception as e:
        await handle_exception(message, e, "process_custom_period_input")


async def generate_and_send_report(
    message: Message,
    state: FSMContext,
    start_date: datetime,
    end_date: datetime,
    selected_period: Optional[str] = None,
) -> None:
    """Генерирует и отправляет отчет."""
    try:
        logger.info(f"Начало генерации отчета за период {start_date} - {end_date}")

        adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
            start_date, end_date
        )

        report_dto = AllUsersReportDTO(
            start_date=adjusted_start,
            end_date=adjusted_end,
            selected_period=selected_period,
        )

        report_parts = await generate_report(report_dto)
        logger.info(f"Отчет сгенерирован, частей: {len(report_parts)}")

        for idx, part in enumerate(report_parts):
            if idx == len(report_parts) - 1:
                part = f"{part}\n\nДля продолжения выберите период, либо нажмите назад"

            await send_html_message_with_kb(
                message=message,
                text=part,
                reply_markup=get_time_period_for_full_report(),
            )

        logger.info("Отчет успешно отправлен пользователю")
    except Exception as e:
        logger.error(f"Ошибка при генерации/отправке отчета: {e}")
        raise


async def generate_report(report_dto: AllUsersReportDTO) -> List[str]:
    """Генерирует отчет используя UseCase."""
    try:
        usecase: GetAllUsersReportUseCase = container.resolve(GetAllUsersReportUseCase)
        return await usecase.execute(dto=report_dto)
    except Exception as e:
        logger.error("Ошибка генерации отчета: %s", str(e), exc_info=True)
        raise
