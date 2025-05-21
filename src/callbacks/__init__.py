from aiogram import Dispatcher

from .user_callback import router as user_callback_router


def register_callback_routers(dispatcher: Dispatcher):
    dispatcher.include_router(user_callback_router)
