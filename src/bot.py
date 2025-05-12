from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from commands import start_commands
from config import settings
from handlers import registry_routers
from middlewares import registry_middlewares


async def init_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await start_commands.set_bot_commands(bot=bot)

    dp = Dispatcher()
    registry_routers(disptcher=dp)
    registry_middlewares(dispatcher=dp)

    return bot, dp
