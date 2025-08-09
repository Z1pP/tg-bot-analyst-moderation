import logging

from aiogram import F, Router, types

from constants import KbCommands

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(F.text == KbCommands.SETTINGS)
async def setting_handler(message: types.Message):
    logger.info("Вызван setting_handler")
    await message.answer(f"Вкладка {KbCommands.SETTINGS} еще в разработке!")
