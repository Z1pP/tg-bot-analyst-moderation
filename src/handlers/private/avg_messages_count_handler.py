import logging

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from constants import CommandList
from container import container
from dto.report import AVGReportDTO
from usecases.report import GetAvgMessageCountUseCase
from utils.command_parser import parse_time, parse_username

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.message(Command(CommandList.REPORT_AVG.name.lower()))
async def report_avg_message_count_handler(message: Message) -> None:
    """
    Обработчик команды /report_avg для получения отчета о среднем количестве сообщений за период.

    """
    try:
        report_dto = break_down_text(text=message.text)

        usecase: GetAvgMessageCountUseCase = container.resolve(
            GetAvgMessageCountUseCase
        )
        report = await usecase.execute(report_dto=report_dto)

        await message.answer(text=report, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Ошибка при обработке команды: {e}")
        await message.answer("Произошла ошибка при обработке команды.")
        return


def break_down_text(text: str) -> AVGReportDTO:
    segments = text.split(" ")

    if len(segments) > 3:
        raise ValueError("Некорректно введена команда")

    time = parse_time(text=segments[1])
    if time is None:
        raise ValueError("Некорректно введено время")

    username = parse_username(text=segments[2])
    if username is None:
        raise ValueError("Некорректно введен username")

    return AVGReportDTO(username=username, time=time)
