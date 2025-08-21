import logging
from datetime import datetime
from typing import List, Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from constants.period import TimePeriod
from container import container
from dto.report import ResponseTimeReportDTO
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


@router.message(
    F.text == KbCommands.GET_REPORT,
    SingleUserReportStates.selected_single_user,
)
async def single_user_report_handler(message: Message, state: FSMContext) -> None:
    """Обработчик запроса на создание отчета о времени ответа."""
    try:
        logger.info(
            f"Пользователь {message.from_user.id} запросил отчет по времени ответа"
        )

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

        logger.info(f"Выбран период для пользователя {user_id}: {message.text}")

        if not user_id:
            logger.warning("Отсутствует user_id в состоянии")

            await send_html_message_with_kb(
                message=message,
                text="Выберите пользователя заново",
                reply_markup=admin_menu_kb(),
            )
            return

        if message.text == TimePeriod.CUSTOM.value:
            logger.info("Запрос пользовательского периода")

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
        logger.info(
            f"Генерация отчета для пользователя {user_id} за период: {start_date} - {end_date}"
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


@router.message(SingleUserReportStates.waiting_cutom_period)
async def process_custom_period_input(message: Message, state: FSMContext) -> None:
    """Обрабатывает ввод пользовательского периода для отчета."""
    try:
        user_data = await state.get_data()
        user_id = user_data.get("user_id")

        logger.info(
            f"Получен пользовательский период для пользователя {user_id}: {message.text}"
        )

        if not user_id:
            logger.warning("Отсутствует user_id при вводе периода")
            await send_html_message_with_kb(
                message=message,
                text="Выберите пользователя заново",
                reply_markup=admin_menu_kb(),
            )
            return

        try:
            start_date, end_date = parse_date(message.text)
            logger.info(f"Парсинг периода успешен: {start_date} - {end_date}")
        except ValueError as e:
            logger.warning(f"Некорректный формат даты: {message.text}, ошибка: {e}")
            await send_html_message_with_kb(
                message=message,
                text=f"❌ Некорректный формат даты: {str(e)}\n"
                "Пожалуйста, введите период в формате DD.MM-DD.MM",
                reply_markup=get_time_period_kb(),
            )
            return

        await generate_and_send_report(
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
        user_data = await state.get_data()
        user_id = user_data.get("user_id")

        logger.info(f"Возврат в меню пользователя {user_id}")

        if not user_id:
            await send_html_message_with_kb(
                message=message,
                text="Выберите пользователя заново",
                reply_markup=admin_menu_kb(),
            )
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


async def generate_and_send_report(
    message: Message,
    state: FSMContext,
    user_id: int,
    start_date: datetime,
    end_date: datetime,
    selected_period: Optional[str] = None,
) -> None:
    """Генерирует и отправляет отчет."""
    try:
        logger.info(
            f"Начало генерации отчета для пользователя {user_id} за "
            f"период {start_date} - {end_date}"
        )

        adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
            start_date, end_date
        )

        report_dto = ResponseTimeReportDTO(
            user_id=user_id,
            start_date=adjusted_start,
            end_date=adjusted_end,
            selected_period=selected_period,
        )

        report_parts = await generate_report(report_dto=report_dto)
        logger.info(
            f"Отчет для пользователя {user_id} сгенерирован, частей: {len(report_parts)}"
        )

        for idx, part in enumerate(report_parts):
            if idx == len(report_parts) - 1:
                part = f"{part}\n\nДля продолжения выберите период, либо нажмите назад"

            await send_html_message_with_kb(
                message=message,
                text=part,
                reply_markup=get_time_period_kb(),
            )

        logger.info(f"Отчет для пользователя {user_id} успешно отправлен")
    except Exception as e:
        logger.error(
            f"Ошибка при генерации/отправке отчета для пользователя {user_id}: {e}"
        )
        await handle_exception(message, e, "generate_and_send_report")


async def generate_report(report_dto: ResponseTimeReportDTO) -> List[str]:
    """Генерирует отчет используя UseCase."""
    try:
        usecase: GetSingleUserReportUseCase = container.resolve(
            GetSingleUserReportUseCase
        )
        return await usecase.execute(report_dto=report_dto)
    except Exception as e:
        logger.error("Ошибка генерации отчета: %s", str(e), exc_info=True)
        raise
