from aiogram import Dispatcher

from .all_chats_callback import router as all_chats_callback_router
from .all_users_callback import router as all_users_callback_router
from .chat_callback import router as chat_callback_router
from .user_callback import router as user_callback_router


def register_callback_routers(dispatcher: Dispatcher):
    dispatcher.include_router(user_callback_router)
    dispatcher.include_router(all_users_callback_router)
    # Регистрация обработчиков для чатов
    dispatcher.include_router(chat_callback_router)
    dispatcher.include_router(all_chats_callback_router)
