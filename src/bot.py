from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from callbacks import register_callback_routers
from commands import start_commands
from config import settings
from handlers import registry_routers
from middlewares import registry_middlewares


async def init_bot() -> tuple[Bot, Dispatcher]:
    print(settings.model_dump())
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await start_commands.set_bot_commands(bot=bot)

    dp = Dispatcher()
    registry_routers(dispatcher=dp)
    registry_middlewares(dispatcher=dp)
    register_callback_routers(dispatcher=dp)

    return bot, dp
