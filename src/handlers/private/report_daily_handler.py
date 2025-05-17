import logging
from datetime import datetime

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from constants import CommandList
from container import container
from dto.report import DailyReportDTO
from usecases.report import GetDailyReportUseCase
from utils.username_validator import validate_username

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.message(Command(CommandList.REPORT_DAILY.name.lower()))
async def report_daily_handler(message: Message) -> None:
    try:
        report_dto = _break_down_text(text=message.text)

        usecase: GetDailyReportUseCase = container.resolve(GetDailyReportUseCase)
        report = await usecase.execute(daily_report_dto=report_dto)

        await message.answer(text=report, parse_mode=ParseMode.HTML)
    except ValueError as e:
        await message.answer(str(e))
        return
    except Exception as e:
        logger.error(f"Ошибка при обработке команды: {e}")
        await message.answer("Произошла ошибка при обработке команды.")
        return


def _break_down_text(text: str) -> DailyReportDTO | None:
    segments = text.split(" ")

    if len(segments) > 3:
        raise ValueError("Некорректно введена команда")

    date = _parse_data(text=segments[1])
    if date is None:
        raise ValueError("Некорректно введены даты")

    username = _parse_username(text=segments[2])
    if username is None:
        raise ValueError("Некорректно введен username")

    return DailyReportDTO(
        username=username,
        start_date=date[0],
        end_date=date[1],
    )


def _parse_data(text: str) -> tuple[datetime, datetime] | None:
    """
    Извлекает даты из текста и возвращает их в формате datetime.
    """
    date = []

    data_segments = text.split("-")

    for data in data_segments:
        day, mounth = data.split(".")
        if not day.isdigit() or not mounth.isdigit():
            return None
        if int(day) > 31 or int(mounth) > 12:
            return None
        date.append(datetime(year=2025, month=int(mounth), day=int(day)))
    if len(date) != 2:
        return None

    if date[0] > date[1]:
        return None

    return date[0], date[1]


def _parse_username(text: str) -> str:
    """
    Извлекает username из текста команды.
    """
    return validate_username(username=text)
