from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.time_service import TimeZoneService

router = Router(name=__name__)


@router.message(Command("time"))
async def start_handler(message: Message):
    await message.answer(
        f"Время на сервере: {TimeZoneService.format_time(TimeZoneService.now())}"
    )
