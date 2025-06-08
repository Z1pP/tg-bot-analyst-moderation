import logging
from datetime import datetime
from typing import Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from constants.period import TimePeriod
from container import container
from dto.report import ResponseTimeReportDTO
from keyboards.reply import get_admin_menu_kb, get_time_period_kb
from keyboards.reply.user_actions import get_user_actions_kb
from services.work_time_service import WorkTimeService
from states.user_states import UserStateManager
from usecases.report import GetResponseTimeReportUseCase
from usecases.report.get_response_time_report_usecase import Report
from utils.command_parser import parse_date
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.message(F.text == KbCommands.REPORT_RESPONSE_TIME)
async def response_time_menu_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик запроса на создание отчета о времени ответа.
    Запрашивает дату для отчета.
    """
    try:
        user_data = await state.get_data()
        username = user_data.get("username")

        if not username:
            # Очищаем состояние
            await state.clear()

            # Просим пользователя заново выбрать модератора
            await send_html_message_with_kb(
                message=message,
                text="Выберите пользователя заново",
                reply_markup=get_admin_menu_kb(),
            )

        # Устанавливаем состояние ожидания выбора периода
        await state.set_state(UserStateManager.report_response_time_selecting_period)

        await send_html_message_with_kb(
            message=message,
            text="Выберите период для отчета",
            reply_markup=get_time_period_kb(),
        )
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="report_daily_handler",
        )


@router.message(
    UserStateManager.report_response_time_selecting_period,
    F.text.in_(TimePeriod.get_all_periods()),
)
async def process_response_time_input(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод даты для отчета о времени ответа.
    """
    try:
        user_data = await state.get_data()
        username = user_data.get("username")

        if not username:
            await state.clear()

            await send_html_message_with_kb(
                message=message,
                text="Выберите пользователя заново",
                reply_markup=get_admin_menu_kb(),
            )

        if message.text == TimePeriod.CUSTOM.value:
            await state.set_state(UserStateManager.report_reponse_time_input_period)

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
            username=username,
            start_date=start_date,
            end_date=end_date,
            selected_period=message.text,
        )

    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="process_response_time_input",
        )


@router.message(UserStateManager.report_reponse_time_input_period)
async def process_custom_period_input(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод пользовательского периода для отчета.
    """
    try:
        user_data = await state.get_data()
        username = user_data.get("username")

        if not username:
            await state.clear()
            await send_html_message_with_kb(
                message=message,
                text="Выберите пользователя заново",
                reply_markup=get_admin_menu_kb(),
            )
            return

        start_date, end_date = parse_date(message.text)

        await generate_and_send_report(
            message=message,
            state=state,
            username=username,
            start_date=start_date,
            end_date=end_date,
        )

    except ValueError as e:
        await send_html_message_with_kb(
            message=message,
            text=f"❌ Некорректный формат даты: {str(e)}\n"
            "Пожалуйста, введите период в формате DD.MM-DD.MM",
            reply_markup=get_time_period_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "process_custom_period_input")


@router.message(
    UserStateManager.report_response_time_selecting_period,
    F.text == KbCommands.BACK,
)
async def back_to_menu_handler(message: Message, state: FSMContext) -> None:
    """Обработчик для возврата в главное меню."""
    try:
        user_data = await state.get_data()
        username = user_data.get("username")

        if not username:
            await state.clear()
            await send_html_message_with_kb(
                message=message,
                text="Выберите пользователя заново",
                reply_markup=get_admin_menu_kb(),
            )
            return

        await state.set_state(UserStateManager.report_menu)
        await send_html_message_with_kb(
            message=message,
            text="Нет так нет.",
            reply_markup=get_user_actions_kb(username=username),
        )
    except Exception as e:
        await handle_exception(message, e, "back_to_menu_handler")


async def generate_and_send_report(
    message: Message,
    state: FSMContext,
    username: str,
    start_date: datetime,
    end_date: datetime,
    selected_period: Optional[str] = None,
) -> None:
    """Генерирует и отправляет отчет."""
    try:
        adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
            start_date, end_date
        )
        report_dto = ResponseTimeReportDTO(
            username=username,
            start_date=adjusted_start,
            end_date=adjusted_end,
            selected_period=selected_period,
        )

        report = await generate_report(report_dto)
        text = f"{report.text}\n\nДля продолжения выберите период, либо нажмите назад"

        await state.set_state(UserStateManager.report_response_time_selecting_period)
        await send_html_message_with_kb(
            message=message,
            text=text,
            reply_markup=get_time_period_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "generate_and_send_report")


async def generate_report(report_dto: ResponseTimeReportDTO) -> Report:
    """
    Генерирует отчет используя UseCase.
    """
    try:
        usecase: GetResponseTimeReportUseCase = container.resolve(
            GetResponseTimeReportUseCase
        )
        return await usecase.execute(report_dto=report_dto)
    except Exception as e:
        logger.error("Ошибка генерации отчета: %s", str(e), exc_info=True)
        raise e
