from aiogram import Dispatcher

from .group.message_handler import router as message_router
from .private.commands_handler import router as commands_router
from .private.report_daily_handler import router as report_daily_router


def registry_routers(disptcher: Dispatcher):
    disptcher.include_router(message_router)
    disptcher.include_router(commands_router)
    disptcher.include_router(report_daily_router)
