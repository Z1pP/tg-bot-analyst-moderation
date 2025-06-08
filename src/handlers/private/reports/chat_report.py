import logging
from datetime import datetime
from typing import Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from constants.period import TimePeriod
from container import container
from dto.report import ChatReportDTO
from keyboards.reply.chat_actions import chat_actions_kb
from keyboards.reply.menu import get_admin_menu_kb
from keyboards.reply.time_period import get_time_period_kb
from services.work_time_service import WorkTimeService
from states import ChatStateManager
from usecases.report import GetReportOnSpecificChat
from utils.command_parser import parse_date
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(
    ChatStateManager.selecting_chat,
    F.text == KbCommands.REPORT_RESPONSE_TIME,
)
async def specific_chat_report(message: Message, state: FSMContext) -> None:
    """Обработчик запроса на создание отчета по конкретному чату."""
    try:
        data = await state.get_data()
        chat_title = data.get("chat_title")

        if not chat_title:
            await select_chat_again(message=message, state=state)
            return

        await state.set_state(ChatStateManager.selecting_period)
        await send_html_message_with_kb(
            text="Выберите период для отчета",
            message=message,
            reply_markup=get_time_period_kb(),
        )
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="specific_chat_report",
        )


@router.message(
    ChatStateManager.selecting_period,
    F.text.in_(TimePeriod.get_all_periods()),
)
async def process_report_input(message: Message, state: FSMContext) -> None:
    """Обрабатывает выбор периода для отчета."""
    try:
        data = await state.get_data()
        chat_title = data.get("chat_title")

        if not chat_title:
            await select_chat_again(message=message, state=state)
            return

        if message.text == TimePeriod.CUSTOM.value:
            await state.set_state(ChatStateManager.selecting_custom_period)
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
            chat_title=chat_title,
            selected_period=message.text,
        )
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="process_report_input",
        )


@router.message(ChatStateManager.selecting_custom_period)
async def process_custom_period_input(message: Message, state: FSMContext) -> None:
    """Обрабатывает ввод пользовательского периода для отчета."""
    try:
        data = await state.get_data()
        chat_title = data.get("chat_title")

        if not chat_title:
            await select_chat_again(message=message, state=state)
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
            await state.set_state(ChatStateManager.selecting_period)
            return

        await generate_and_send_report(
            message=message,
            state=state,
            start_date=start_date,
            end_date=end_date,
            chat_title=chat_title,
            selected_period=message.text,
        )
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="process_custom_period_input",
        )


@router.message(
    ChatStateManager.selecting_period,
    F.text == KbCommands.BACK,
)
async def back_to_menu_handler(message: Message, state: FSMContext) -> None:
    """Обработчик для возврата в меню чата."""
    try:
        data = await state.get_data()
        chat_title = data.get("chat_title")

        if not chat_title:
            await select_chat_again(message=message, state=state)
            return

        await state.set_state(ChatStateManager.selecting_chat)
        await send_html_message_with_kb(
            message=message,
            text="Возврат к меню чата.",
            reply_markup=chat_actions_kb(chat_title=chat_title),
        )
    except Exception as e:
        await handle_exception(message, e, "back_to_menu_handler")


async def select_chat_again(message: Message, state: FSMContext) -> None:
    """Повторно запрашивает выбор чата."""
    await state.clear()
    await send_html_message_with_kb(
        message=message,
        text="Выберите чат заново",
        reply_markup=get_admin_menu_kb(),
    )


async def generate_and_send_report(
    message: Message,
    state: FSMContext,
    start_date: datetime,
    end_date: datetime,
    chat_title: str,
    selected_period: Optional[str] = None,
) -> None:
    """Генерирует и отправляет отчет по чату."""
    try:
        adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
            start_date, end_date
        )

        report_dto = ChatReportDTO(
            chat_title=chat_title,
            start_date=adjusted_start,
            end_date=adjusted_end,
            selected_period=selected_period,
        )

        report = await generate_report(report_dto)
        text = f"{report}\n\nДля продолжения выберите период, либо нажмите назад"

        await state.set_state(ChatStateManager.selecting_period)
        await send_html_message_with_kb(
            message=message,
            text=text,
            reply_markup=get_time_period_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "generate_and_send_report")


async def generate_report(report_dto: ChatReportDTO) -> str:
    """Генерирует отчет используя UseCase."""
    try:
        usecase: GetReportOnSpecificChat = container.resolve(GetReportOnSpecificChat)
        return await usecase.execute(dto=report_dto)
    except Exception as e:
        logger.error("Ошибка генерации отчета: %s", str(e), exc_info=True)
        raise e
