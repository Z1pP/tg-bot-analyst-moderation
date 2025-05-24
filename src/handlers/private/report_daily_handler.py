import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from container import container
from dto.report import DailyReportDTO
from keyboards.reply.menu import get_moderators_list_kb
from states.user_states import UserManagement
from usecases.report import GetDailyReportUseCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.message(F.text == KbCommands.REPORT_DAILY)
async def report_daily_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик запроса на создание ежедневного отчета.
    Запрашивает период для отчета.
    """
    user_data = await state.get_data()
    username = user_data.get("username")

    await state.set_state(UserManagement.report_daily_selecting_period)

    if username:
        await send_html_message_with_kb(
            message=message,
            text="Введите период для отчета в формате DD.MM-DD.MM\n"
            "Например: 16.04-20.04 или 16.04- (с 16.04 до сегодня)",
        )

    else:
        await state.clear()
        await send_html_message_with_kb(
            message=message,
            text="Выберите пользователя заново",
            reply_markup=get_moderators_list_kb(),
        )


@router.message(UserManagement.report_daily_selecting_period)
async def process_daily_report_input(message: Message, state: FSMContext) -> None:
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

        parts = message.text.split()

        date_part = parts[0] if parts else ""

        # Проверяем формат даты
        if "-" not in date_part:
            await message.answer(
                "Некорректный формат периода. Используйте формат DD.MM-DD.MM или DD.MM-"
            )
            return

        # Разбираем период
        start_str, end_str = date_part.split("-")

        # Парсим начальную дату
        try:
            if "." not in start_str or len(start_str.split(".")) != 2:
                await message.answer(
                    "Некорректный формат начальной даты. Используйте DD.MM"
                )
                return

            day, month = map(int, start_str.split("."))
            current_year = datetime.now().year
            start_date = datetime(current_year, month, day)
        except (ValueError, IndexError):
            await message.answer(
                "Некорректный формат начальной даты. Используйте DD.MM"
            )
            return

        # Парсим конечную дату
        if end_str:
            try:
                if "." not in end_str or len(end_str.split(".")) != 2:
                    await message.answer(
                        "Некорректный формат конечной даты. Используйте DD.MM"
                    )
                    return

                day, month = map(int, end_str.split("."))
                current_year = datetime.now().year
                end_date = datetime(current_year, month, day, 23, 59, 59)
            except (ValueError, IndexError):
                await message.answer(
                    "Некорректный формат конечной даты. Используйте DD.MM"
                )
                return
        else:
            end_date = datetime.now()

        # Проверяем, что конечная дата не раньше начальной
        if end_date < start_date:
            await message.answer("Конечная дата не может быть раньше начальной!")
            return

        report_dto = DailyReportDTO(
            username=username, start_date=start_date, end_date=end_date
        )

        usecase = container.resolve(GetDailyReportUseCase)
        report = await usecase.execute(daily_report_dto=report_dto)

        await state.set_state(UserManagement.viewing_user)

        # Отправляем отчет
        await send_html_message_with_kb(
            message=message,
            text=report,
        )
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="process_daily_report_input",
        )
