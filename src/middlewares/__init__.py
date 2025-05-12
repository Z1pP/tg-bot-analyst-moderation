from aiogram import Dispatcher

from .chat_middleware import ChatSessionMiddleware
from .moderator_middleware import ModeratorIdentityMiddleware


def registry_middlewares(dispatcher: Dispatcher) -> None:
    dispatcher.message.middleware(ModeratorIdentityMiddleware())
    dispatcher.message.middleware(ChatSessionMiddleware())
