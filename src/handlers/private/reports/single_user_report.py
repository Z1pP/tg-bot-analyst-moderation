import logging
from datetime import datetime
from typing import Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from constants.period import TimePeriod
from container import container
from dto.report import SingleUserReportDTO
from keyboards.inline import order_details_kb
from keyboards.reply import admin_menu_kb, get_time_period_kb
from keyboards.reply.user_actions import user_actions_kb
from services.work_time_service import WorkTimeService
from states import SingleUserReportStates
from usecases.report import GetSingleUserReportUseCase
from utils.command_parser import parse_date
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


async def _validate_user_id(message: Message, state: FSMContext) -> Optional[int]:
    """Валидирует наличие user_id в состоянии."""
    user_data = await state.get_data()
    user_id = user_data.get("user_id")

    if not user_id:
        await send_html_message_with_kb(
            message=message,
            text="Выберите пользователя заново",
            reply_markup=admin_menu_kb(),
        )

    return user_id


@router.message(
    F.text == KbCommands.GET_REPORT,
    SingleUserReportStates.selected_single_user,
)
async def single_user_report_handler(message: Message, state: FSMContext) -> None:
    """Обработчик запроса на создание отчета о времени ответа."""
    try:
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
        user_id = await _validate_user_id(message, state)
        if not user_id:
            return

        if message.text == TimePeriod.CUSTOM.value:
            await log_and_set_state(
                message=message,
                state=state,
                new_state=SingleUserReportStates.waiting_cutom_period,
            )

            await send_html_message_with_kb(
                message=message,
                text="Введите период в формате DD.MM-DD.MM\n"
                "Например: 16.04-20.04 или 16.04- (с 16.04 до сегодня)",
            )
            return

        start_date, end_date = TimePeriod.to_datetime(period=message.text)
        await _generate_and_send_report(
            message=message,
            state=state,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            selected_period=message.text,
        )
    except Exception as e:
        await handle_exception(message, e, "process_period_selection")


@router.message(SingleUserReportStates.waiting_cutom_period)
async def process_custom_period_input(message: Message, state: FSMContext) -> None:
    """Обрабатывает ввод пользовательского периода для отчета."""
    try:
        user_id = await _validate_user_id(message, state)
        if not user_id:
            return

        try:
            start_date, end_date = parse_date(message.text)
        except ValueError as e:
            await send_html_message_with_kb(
                message=message,
                text=f"❌ Некорректный формат даты: {str(e)}\n"
                "Пожалуйста, введите период в формате DD.MM-DD.MM",
                reply_markup=get_time_period_kb(),
            )
            return

        await _generate_and_send_report(
            message=message,
            state=state,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        await log_and_set_state(
            message=message,
            state=state,
            new_state=SingleUserReportStates.selecting_period,
        )
    except Exception as e:
        await handle_exception(message, e, "process_custom_period_input")


@router.message(
    SingleUserReportStates.selecting_period,
    F.text == KbCommands.BACK,
)
async def back_to_menu_handler(message: Message, state: FSMContext) -> None:
    """Обработчик для возврата в меню пользователя."""
    try:
        user_id = await _validate_user_id(message, state)
        if not user_id:
            return

        await log_and_set_state(
            message=message,
            state=state,
            new_state=SingleUserReportStates.selected_single_user,
        )

        await send_html_message_with_kb(
            message=message,
            text="Возвращаемся в меню",
            reply_markup=user_actions_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "back_to_menu_handler")


async def _generate_and_send_report(
    message: Message,
    state: FSMContext,
    user_id: int,
    start_date: datetime,
    end_date: datetime,
    selected_period: Optional[str] = None,
) -> None:
    """Генерирует и отправляет отчет."""
    adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
        start_date, end_date
    )

    report_dto = SingleUserReportDTO(
        user_id=user_id,
        admin_tg_id=str(message.from_user.id),
        start_date=adjusted_start,
        end_date=adjusted_end,
        selected_period=selected_period,
    )

    usecase: GetSingleUserReportUseCase = container.resolve(GetSingleUserReportUseCase)
    is_single_day = usecase.is_single_day_report(report_dto)
    report_parts = await usecase.execute(report_dto=report_dto)

    # Сохраняем report_dto для детализации (только для многодневных отчетов)
    if not is_single_day:
        await state.update_data(report_dto=report_dto)

    for idx, part in enumerate(report_parts):
        if idx == len(report_parts) - 1:
            part = f"{part}"

        await send_html_message_with_kb(
            message=message,
            text=part,
            reply_markup=order_details_kb(show_details=not is_single_day),
        )
