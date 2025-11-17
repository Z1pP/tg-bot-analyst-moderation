from aiogram import Dispatcher, Router
from aiogram.enums import ChatType

from container import container
from filters import AdminOnlyFilter, ChatTypeFilter, GroupTypeFilter
from middlewares import AdminAntispamMiddleware
from services.caching import ICache

from .group import router as group_router
from .private import router as private_router


def registry_admin_routers(dispatcher: Dispatcher):
    # Создаем роутер для админов
    only_admin_router = Router(name="admin_router")

    # Регистрируем фильтры: только для приватных чатов и только для админов
    only_admin_router.message.filter(
        ChatTypeFilter(chat_type=[ChatType.PRIVATE]),
        AdminOnlyFilter(),
    )

    # Регистрируем антиспам middleware
    cache: ICache = container.resolve(ICache)
    only_admin_router.message.middleware(AdminAntispamMiddleware(cache))

    # Регистрируем приватный роутер
    only_admin_router.include_router(private_router)

    # Регистрируем роутер для админов
    dispatcher.include_router(only_admin_router)


def registry_group_routers(dispatcher: Dispatcher):
    # Регистриуем групповой роутер
    public_router = Router(name="public_router")
    public_router.message.filter(GroupTypeFilter())

    public_router.include_router(group_router)

    dispatcher.include_router(public_router)


def registry_routers(dispatcher: Dispatcher):
    registry_admin_routers(dispatcher)
    registry_group_routers(dispatcher)
