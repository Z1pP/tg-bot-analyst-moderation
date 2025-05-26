import logging
from typing import Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants.period import TimePeriod
from container import container
from dto.report import AVGReportDTO
from keyboards.reply import get_moderators_list_kb, get_time_period_kb
from keyboards.reply.user_actions import KbCommands
from states.user_states import UserManagement
from usecases.report import GetAvgMessageCountUseCase
from utils.command_parser import parse_date
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)

logger = logging.getLogger(name=__name__)


@router.message(F.text == KbCommands.REPORT_AVG)
async def report_avg_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик запроса на создание отчета о средних сообщениях.
    Запрашивает период для отчета.
    """

    try:
        user_data = await state.get_data()
        username = user_data.get("username")

        await state.set_state(UserManagement.report_avg_selecting_period)

        if not username:
            # Очищаем состояние
            await state.clear()

            await send_html_message_with_kb(
                message=message,
                text="Выберите пользователя заново",
                reply_markup=get_moderators_list_kb(),
            )
            return

        # Устанавливаем состояние ожидания выбора периода
        await state.set_state(UserManagement.report_avg_selecting_period)

        await send_html_message_with_kb(
            message=message,
            text="Выберите период для отчета",
            reply_markup=get_time_period_kb(),
        )

    except Exception as e:
        await handle_exception(
            message,
            e,
            context="report_avg_handler",
        )


@router.message(
    UserManagement.report_avg_selecting_period,
    F.text.in_(
        TimePeriod.get_all_periods(),
    ),
)
async def process_avg_report_input(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод периода и пользователя для отчета.
    """
    try:
        user_data = await state.get_data()
        username = user_data.get("username")

        if not username:
            await state.clear()

            await send_html_message_with_kb(
                message=message,
                text="Выберите пользователя заново",
                reply_markup=get_moderators_list_kb(),
            )

        if message.text == TimePeriod.CUSTOM.value:
            await state.set_state(UserManagement.report_avg_waiting_input_period)

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
            context="process_avg_report_input",
        )


@router.message(UserManagement.report_avg_waiting_input_period)
async def process_daily_report_period(message: Message, state: FSMContext) -> None:
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
                reply_markup=get_moderators_list_kb(),
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
        await handle_exception(message, e, "process_daily_report_period")


async def generate_and_send_report(
    message: Message,
    state: FSMContext,
    username: str,
    start_date,
    end_date,
    selected_period: Optional[str] = None,
) -> None:
    """
    Генерирует и отправляет отчет.
    """
    report_dto = AVGReportDTO(
        username=username,
        start_date=start_date,
        end_date=end_date,
        selected_period=selected_period,
    )

    report = await generate_report(report_dto)
    text = f"{report}\n\nДля продолжения выберите период, либо нажмите назад"

    await state.set_state(UserManagement.report_daily_selecting_period)
    await send_html_message_with_kb(
        message=message,
        text=text,
        reply_markup=get_time_period_kb(),
    )


async def generate_report(report_dto: AVGReportDTO) -> str:
    """
    Генерирует отчет используя UseCase.
    """
    try:
        usecase: GetAvgMessageCountUseCase = container.resolve(
            GetAvgMessageCountUseCase
        )
        return await usecase.execute(report_dto=report_dto)
    except Exception as e:
        logger.error("Ошибка генерации отчета: %s", str(e), exc_info=True)
        raise e
