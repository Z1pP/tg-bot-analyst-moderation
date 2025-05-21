import logging
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from constants import CommandList
from container import container
from dto.report import ResponseTimeReportDTO
from usecases.report import GetResponseTimeReportUseCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.username_validator import validate_username

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.message(Command(CommandList.REPORT_RESPONSE_TIME.name.lower()))
async def response_time_report_handler(message: Message) -> None:
    """
    Обработчик команды /report_response_time для получения отчета о времени ответа.
    Формат: /report_response_time @username [DD.MM.YYYY]
    """
    try:
        report_dto = parse_command(message.text)
        usecase = container.resolve(GetResponseTimeReportUseCase)
        report = await usecase.execute(report_dto=report_dto)
        await send_html_message_with_kb(message=message, text=report)
    except Exception as e:
        logger.error(f"Ошибка при обработке команды: {e}")
        await handle_exception(message, e)


def parse_command(text: str) -> ResponseTimeReportDTO:
    """
    Парсит команду для отчета о времени ответа.
    Формат: /report_response_time @username [DD.MM]
    """
    segments = text.split()

    if len(segments) < 2 or len(segments) > 3:
        raise ValueError(
            "Неверный формат команды. Используйте: /report_response_time @username [DD.MM]"
        )

    # Парсим username
    username = validate_username(segments[1])
    if not username:
        raise ValueError("Некорректное имя пользователя")

    # Парсим дату (если указана)
    report_date = None
    if len(segments) == 3:
        try:
            day, month = map(int, segments[2].split("."))
            report_date = datetime(year=2025, month=month, day=day).date()
        except (ValueError, IndexError):
            raise ValueError("Некорректный формат даты. Используйте формат DD.MM")

    return ResponseTimeReportDTO(username=username, report_date=report_date)
