import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from constants import CommandList
from container import container
from dto.report import ResponseTimeReportDTO
from usecases.report import GetResponseTimeReportUseCase
from utils.command_parser import parse_days, parse_username
from utils.send_message import send_html_message

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.message(Command(CommandList.REPORT_RESPONSE_TIME.name.lower()))
async def response_time_report_handler(message: Message) -> None:
    try:
        report_dto = parse_command(text=message.text)

        usecase: GetResponseTimeReportUseCase = container.resolve(
            GetResponseTimeReportUseCase
        )
        report = await usecase.execute(report_dto=report_dto)

        await send_html_message(message=message, text=report)
    except ValueError as e:
        await message.answer(str(e))
        return
    except Exception as e:
        logger.error(f"Ошибка при обработке команды: {e}")
        await message.answer("Произошла ошибка при обработке команды.")
        return


def parse_command(text: str) -> ResponseTimeReportDTO:
    segments = text.split(" ")

    if len(segments) == 2:
        # Значит что количество дней явно не указано, начит days = 7
        username = parse_username(text=segments[1])

        return ResponseTimeReportDTO(
            username=username,
        )
    elif len(segments) == 3:
        # Указано явно количество дней и username
        total_days = parse_days(text=segments[2])
        if total_days is None:
            raise ValueError("Некорректно введено количество дней")

        username = parse_username(text=segments[1])
        if username is None:
            raise ValueError("Некорректно введен @username")

        return ResponseTimeReportDTO(
            username=username,
            days=total_days,
        )
    else:
        raise ValueError("Некорректно введена команда")
