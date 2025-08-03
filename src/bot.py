from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from callbacks import register_callback_routers
from commands import start_commands
from config import settings
from handlers import registry_routers


async def init_bot() -> tuple[Bot, Dispatcher]:
    print(settings.model_dump())
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Создаем хранилище
    storage = MemoryStorage()

    await start_commands.set_bot_commands(bot=bot)

    dp = Dispatcher(storage=storage)
    registry_routers(dispatcher=dp)
    register_callback_routers(dispatcher=dp)

    return bot, dp
