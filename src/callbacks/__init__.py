from aiogram import Dispatcher

from .categories import router as categories_router
from .chats import router as chats_router
from .templates import router as templates_router  # noqa: F401
from .users import router as users_router


def register_callback_routers(dispatcher: Dispatcher):
    dispatcher.include_router(users_router)
    dispatcher.include_router(chats_router)
    dispatcher.include_router(categories_router)
    dispatcher.include_router(templates_router)
