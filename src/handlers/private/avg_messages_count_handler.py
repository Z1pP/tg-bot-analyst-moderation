import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from container import container
from dto.report import AVGReportDTO
from keyboards.reply.menu import get_back_kb, get_moderators_list_kb
from keyboards.reply.user_actions import KbCommands
from states.user_states import UserManagement
from usecases.report import GetAvgMessageCountUseCase
from utils.command_parser import parse_time
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

    user_data = await state.get_data()
    username = user_data.get("username")

    await state.set_state(UserManagement.report_avg_selecting_period)

    if username:
        await state.update_data(report_username=username)
        await send_html_message_with_kb(
            message=message,
            text="Введите период для отчета в формате:\n"
            "• <b>Xh</b> - часы (например, 6h)\n"
            "• <b>Xd</b> - дни (например, 1d)\n"
            "• <b>Xw</b> - недели (например, 2w)\n"
            "• <b>Xm</b> - месяцы (например, 1m)",
        )

    else:
        await state.clear()
        await send_html_message_with_kb(
            message=message,
            text="Выберите пользователя заново",
            reply_markup=get_moderators_list_kb(),
        )


@router.message(UserManagement.report_avg_selecting_period)
async def process_avg_report_input(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод периода и пользователя для отчета о средних сообщениях.
    """
    try:
        user_data = await state.get_data()
        saved_username = user_data.get("username")

        time = parse_time(text=message.text)

        report_dto = AVGReportDTO(
            username=saved_username,
            time=time,
        )
        usecase: GetAvgMessageCountUseCase = container.resolve(
            GetAvgMessageCountUseCase
        )

        # Формируем отчет
        report = await usecase.execute(report_dto=report_dto)

        text = report + (
            "\n\nДля продолжения укажите дату, либо выберите другой раздел ниже"
        )

        await send_html_message_with_kb(
            message=message,
            text=text,
            reply_markup=get_back_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, context="process_avg_report_input")
