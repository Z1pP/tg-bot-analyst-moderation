from aiogram import Dispatcher

from .chats import router as chats_router
from .moderators import router as moderators_router


def register_callback_routers(dispatcher: Dispatcher):
    # Регистрация обработчиков для модераторов
    dispatcher.include_router(moderators_router)

    # Регистрация обработчиков для чатов
    dispatcher.include_router(chats_router)
