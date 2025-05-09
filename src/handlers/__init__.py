from aiogram import Dispatcher

from .group.message_handler import router as message_router


def registry_routers(disptcher: Dispatcher):
    disptcher.include_router(message_router)
