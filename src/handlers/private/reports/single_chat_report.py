import logging
from datetime import datetime
from typing import List, Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from constants.period import TimePeriod
from container import container
from dto.report import ChatReportDTO
from keyboards.inline import order_details_kb
from keyboards.reply import admin_menu_kb, chat_actions_kb, get_time_period_kb
from services.work_time_service import WorkTimeService
from states import ChatStateManager
from usecases.report import GetReportOnSpecificChatUseCase
from utils.command_parser import parse_date
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(
    ChatStateManager.selecting_chat,
    F.text == KbCommands.GET_REPORT,
)
async def single_chat_report_handler(message: Message, state: FSMContext) -> None:
    """Обработчик запроса на создание отчета по конкретному чату."""
    try:
        data = await state.get_data()
        chat_id = data.get("chat_id")

        if not chat_id:
            logger.warning("Отсутствует название чата в состоянии")
            await select_chat_again(message=message, state=state)
            return
        logger.info(
            f"Пользователь {message.from_user.username} запросил отчет "
            f"по чату с chat_id={chat_id}"
        )

        await log_and_set_state(
            message=message,
            state=state,
            new_state=ChatStateManager.selecting_period,
        )

        await send_html_message_with_kb(
            text="Выберите период для отчета",
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

        logger.info(f"Выбран период для чата chat_id={chat_id}: {message.text}")

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

            await send_html_message_with_kb(
                message=message,
                text="Введите период в формате DD.MM-DD.MM\n"
                "Например: 16.04-20.04 или 16.04- (с 16.04 до сегодня)",
            )
            return

        start_date, end_date = TimePeriod.to_datetime(message.text)
        logger.info(
            f"Генерация отчета по чату chat_id={chat_id} "
            f"за период: {start_date} - {end_date}"
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


@router.message(ChatStateManager.selecting_custom_period)
async def process_custom_period_input(message: Message, state: FSMContext) -> None:
    """Обрабатывает ввод пользовательского периода для отчета."""
    try:
        data = await state.get_data()
        chat_id = data.get("chat_id")

        logger.info(
            f"Получен пользовательский период для чата chat_id={chat_id}: {message.text}"
        )

        if not chat_id:
            logger.warning("Отсутствует chat_id при вводе периода")
            await select_chat_again(message=message, state=state)
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
            await state.set_state(ChatStateManager.selecting_period)
            return

        await generate_and_send_report(
            message=message,
            state=state,
            start_date=start_date,
            end_date=end_date,
            chat_id=chat_id,
            selected_period=message.text,
        )
    except Exception as e:
        await handle_exception(message, e, "process_custom_period_input")


@router.message(
    ChatStateManager.selecting_period,
    F.text == KbCommands.BACK,
)
async def back_to_menu_handler(message: Message, state: FSMContext) -> None:
    """Обработчик для возврата в меню чата."""
    try:
        data = await state.get_data()
        chat_id = data.get("chat_id")

        if not chat_id:
            await select_chat_again(message=message, state=state)
            return

        await log_and_set_state(
            message=message,
            state=state,
            new_state=ChatStateManager.selecting_chat,
        )

        await send_html_message_with_kb(
            message=message,
            text="Возврат к меню чата.",
            reply_markup=chat_actions_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "back_to_menu_handler")


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
        text="Выберите чат заново",
        reply_markup=admin_menu_kb(),
    )


async def generate_and_send_report(
    message: Message,
    state: FSMContext,
    start_date: datetime,
    end_date: datetime,
    chat_id: int,
    selected_period: Optional[str] = None,
) -> None:
    """Генерирует и отправляет отчет по чату."""
    try:
        logger.info(
            f"Начало генерации отчета по чату {chat_id} за период {start_date} - {end_date}"
        )

        adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
            start_date, end_date
        )

        report_dto = ChatReportDTO(
            chat_id=chat_id,
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
            f"Отчет по чату {chat_id} сгенерирован, частей: {len(report_parts)}"
        )

        # Сохраняем report_dto для детализации (только для многодневных отчетов)
        if not is_single_day:
            await state.update_data(chat_report_dto=report_dto)

        await state.set_state(ChatStateManager.selecting_period)

        for idx, part in enumerate(report_parts):
            if idx == len(report_parts) - 1:
                part = f"{part}\n\nДля продолжения выберите период, либо нажмите назад"

            await send_html_message_with_kb(
                message=message,
                text=part,
                reply_markup=order_details_kb(show_details=not is_single_day),
            )

        logger.info(f"Отчет по чату {chat_id} успешно отправлен")
    except Exception as e:
        logger.error(f"Ошибка при генерации/отправке отчета по чату {chat_id}: {e}")
        await handle_exception(message, e, "generate_and_send_report")



