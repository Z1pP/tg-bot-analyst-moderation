from aiogram import Dispatcher

from .chat_middleware import ChatSessionMiddleware
from .moderator_middleware import UserIdentityMiddleware


def registry_middlewares(dispatcher: Dispatcher) -> None:
    dispatcher.message.middleware(UserIdentityMiddleware())
    dispatcher.message.middleware(ChatSessionMiddleware())
