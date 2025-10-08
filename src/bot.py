from aiogram import Bot, Dispatcher

from callbacks import register_callback_routers
from commands import start_commands
from di import container
from handlers import registry_routers
from utils.exception_handler import registry_exceptions


async def configure_dispatcher() -> tuple[Bot, Dispatcher]:
    bot: Bot = container.resolve(Bot)
    dp: Dispatcher = container.resolve(Dispatcher)

    await start_commands.set_bot_commands(bot=bot)

    registry_routers(dispatcher=dp)
    register_callback_routers(dispatcher=dp)
    registry_exceptions(dispatcher=dp)

    return bot, dp
