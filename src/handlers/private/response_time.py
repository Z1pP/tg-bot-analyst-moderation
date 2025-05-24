import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from container import container
from dto.report import ResponseTimeReportDTO
from keyboards.reply.menu import get_moderators_list_kb
from services.time_service import TimeZoneService
from states.user_states import UserManagement
from usecases.report import GetResponseTimeReportUseCase
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
    # Получаем данные о выбранном пользователе, если есть
    user_data = await state.get_data()
    username = user_data.get("username")

    if not username:
        # Если пользователь не выбран, показываем список модераторов
        await state.clear()
        await send_html_message_with_kb(
            message=message,
            text="Выберите пользователя:",
            reply_markup=get_moderators_list_kb(),
        )
        return

    # Пользователь выбран, запрашиваем дату
    await state.set_state(UserManagement.report_response_time_selecting_date)
    await state.update_data(report_username=username)
    await message.answer(
        "Введите дату для отчета в формате DD.MM\n"
        "Например: 16.04\n\n"
        "Или введите 'now' или 'n' для получения отчета за сегодня"
    )


@router.message(UserManagement.report_response_time_selecting_date)
async def process_response_time_input(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод даты для отчета о времени ответа.
    """
    try:
        # Получаем данные из состояния
        user_data = await state.get_data()
        username = user_data.get("username")

        # Если нет username, перенаправляем в главное меню
        if not username:
            await state.clear()
            await send_html_message_with_kb(
                message=message,
                text="Выберите пользователя:",
                reply_markup=get_moderators_list_kb(),
            )
            return

        report_date = await parse_report_date(message)
        # Формируем отчет
        report_dto = ResponseTimeReportDTO(username=username, report_date=report_date)

        usecase: GetResponseTimeReportUseCase = container.resolve(
            GetResponseTimeReportUseCase
        )

        # Получаем отчет
        report = await usecase.execute(report_dto=report_dto)

        # Возвращаемся в состояние просмотра пользователя
        await state.set_state(UserManagement.viewing_user)

        # Отправляем отчет
        await send_html_message_with_kb(message=message, text=report)
    except Exception as e:
        logger.error(f"Ошибка при обработке ввода для отчета: {e}")
        await handle_exception(message, e)

        # При ошибке перенаправляем в главное меню
        await state.clear()
        await send_html_message_with_kb(
            message=message,
            text="Произошла ошибка. Выберите пользователя заново:",
            reply_markup=get_moderators_list_kb(),
        )


async def parse_report_date(message: Message):
    text = message.text.strip().lower()

    if text == "now" or text == "n":
        return None

    # Если пользователь ввел дату
    elif "." in text:
        try:
            day, month = map(int, text.split("."))
            current_year = TimeZoneService.now().year()
            return datetime(current_year, month, day).date()
        except (ValueError, IndexError):
            await message.answer(
                "Некорректный формат даты. Используйте формат DD.MM или 'now'"
            )
            return
    else:
        await message.answer(
            "Некорректный формат даты. Используйте формат DD.MM или 'now'"
        )
        return
