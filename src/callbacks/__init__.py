from aiogram import Dispatcher

from .chats import router as chats_router
from .reports import router as reports_router
from .users import router as users_router


def register_callback_routers(dispatcher: Dispatcher):
    dispatcher.include_router(users_router)
    dispatcher.include_router(chats_router)
    dispatcher.include_router(reports_router)
