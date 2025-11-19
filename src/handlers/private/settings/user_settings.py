import logging

from aiogram import Router

# from constants import Dialog

router = Router(name=__name__)
logger = logging.getLogger(__name__)


# @router.message(F.text == Dialog.Menu.SETTINGS)
# async def setting_handler(message: types.Message):
#     logger.info("Вызван setting_handler")
#     await message.answer(f"Вкладка {Dialog.Menu.SETTINGS} еще в разработке!")
