from aiogram import Bot, Dispatcher

from di import container
from handlers import registry_routers
from utils.exception_handler import registry_exceptions


async def configure_dispatcher() -> tuple[Bot, Dispatcher]:
    bot: Bot = container.resolve(Bot)
    dp: Dispatcher = container.resolve(Dispatcher)

    registry_routers(dispatcher=dp)
    registry_exceptions(dispatcher=dp)

    return bot, dp
