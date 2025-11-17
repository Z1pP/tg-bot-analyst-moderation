from aiogram import Bot, Dispatcher

from di import container
from handlers import registry_routers
from middlewares import LanguageMiddleware
from services.user import UserService
from utils.exception_handler import registry_exceptions


async def configure_dispatcher() -> tuple[Bot, Dispatcher]:
    bot: Bot = container.resolve(Bot)
    dp: Dispatcher = container.resolve(Dispatcher)

    user_service: UserService = container.resolve(UserService)
    language_middleware = LanguageMiddleware(user_service)
    dp.message.middleware(language_middleware)
    dp.callback_query.middleware(language_middleware)

    registry_routers(dispatcher=dp)
    registry_exceptions(dispatcher=dp)

    return bot, dp
