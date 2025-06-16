import logging
from datetime import datetime
from typing import Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from constants.period import TimePeriod
from container import container
from dto.report import AllModeratorReportDTO
from keyboards.reply import get_time_period_for_full_report
from services.work_time_service import WorkTimeService
from states.user_states import UserStateManager
from usecases.report import GetAllModeratorsReportUseCase
from utils.command_parser import parse_date
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.message(F.text == KbCommands.FULL_REPORT)
async def full_report_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик который отображает отчет по всем модераторам за раз
    """
    try:
        # Устанавливаем состояние ожидания выбора периода
        await state.set_state(UserStateManager.report_full_selecting_period)

        await send_html_message_with_kb(
            message=message,
            text="Выберите период для отчета",
            reply_markup=get_time_period_for_full_report(),
        )
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="report_daily_handler",
        )


@router.message(
    UserStateManager.report_full_selecting_period,
    F.text.in_(TimePeriod.get_all_periods()),
)
async def process_full_report_input(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод периода и пользователя для отчета.
    """
    try:
        if message.text == TimePeriod.CUSTOM.value:
            await state.set_state(UserStateManager.report_full_waiting_input_period)

            await send_html_message_with_kb(
                message=message,
                text="Введите период в формате DD.MM-DD.MM\n"
                "Например: 16.04-20.04 или 16.04- (с 16.04 до сегодня)",
            )
            return

        start_date, end_date = TimePeriod.to_datetime(message.text)

        await generate_and_send_report(
            message=message,
            state=state,
            start_date=start_date,
            end_date=end_date,
            selected_period=message.text,
        )

    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="process_full_report_input",
        )


@router.message(UserStateManager.report_full_waiting_input_period)
async def process_full_report_period(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод пользовательского периода для отчета.
    """
    try:
        start_date, end_date = parse_date(message.text)

        await generate_and_send_report(
            message=message,
            state=state,
            start_date=start_date,
            end_date=end_date,
        )

    except ValueError as e:
        await send_html_message_with_kb(
            message=message,
            text=f"❌ Некорректный формат даты: {str(e)}\n"
            "Пожалуйста, введите период в формате DD.MM-DD.MM",
            reply_markup=get_time_period_for_full_report(),
        )
    except Exception as e:
        await handle_exception(message, e, "process_full_report_period")


async def generate_and_send_report(
    message: Message,
    state: FSMContext,
    start_date: datetime,
    end_date: datetime,
    selected_period: Optional[str] = None,
) -> None:
    """
    Генерирует и отправляет отчет.
    """

    adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
        start_date, end_date
    )

    report_dto = AllModeratorReportDTO(
        start_date=adjusted_start,
        end_date=adjusted_end,
        selected_period=selected_period,
    )

    report_parts = await generate_report(report_dto)

    await state.set_state(UserStateManager.report_full_selecting_period)

    for idx, part in enumerate(report_parts):
        if idx == len(report_parts) - 1:
            part = f"{part}\n\nДля продолжения выберите период, либо нажмите назад"

        await send_html_message_with_kb(
            message=message,
            text=part,
            reply_markup=get_time_period_for_full_report(),
        )


async def generate_report(report_dto: AllModeratorReportDTO) -> str:
    """
    Генерирует отчет используя UseCase.
    """
    try:
        usecase: GetAllModeratorsReportUseCase = container.resolve(
            GetAllModeratorsReportUseCase
        )
        return await usecase.execute(dto=report_dto)
    except Exception as e:
        logger.error("Ошибка генерации отчета: %s", str(e), exc_info=True)
        raise e
