import logging

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from constants import CommandList
from container import container
from dto.report import DailyReportDTO
from usecases.report import GetDailyReportUseCase
from utils.command_parser import parse_data, parse_username

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.message(Command(CommandList.REPORT_DAILY.name.lower()))
async def report_daily_handler(message: Message) -> None:
    try:
        report_dto = break_down_text(text=message.text)

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


def break_down_text(text: str) -> DailyReportDTO:
    segments = text.split(" ")

    if len(segments) > 3:
        raise ValueError("Некорректно введена команда")

    date = parse_data(text=segments[1])
    if date is None:
        raise ValueError("Некорректно введены даты")

    username = parse_username(text=segments[2])
    if username is None:
        raise ValueError("Некорректно введен username")

    return DailyReportDTO(
        username=username,
        start_date=date[0],
        end_date=date[1],
    )
