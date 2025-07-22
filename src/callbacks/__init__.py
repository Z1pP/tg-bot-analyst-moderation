from aiogram import Dispatcher

from .categories import router as categories_router
from .chats import router as chats_router
from .moderators import router as moderators_router
from .templates import router as templates_router  # noqa: F401


def register_callback_routers(dispatcher: Dispatcher):
    dispatcher.include_router(moderators_router)
    dispatcher.include_router(chats_router)
    dispatcher.include_router(categories_router)
    dispatcher.include_router(templates_router)
