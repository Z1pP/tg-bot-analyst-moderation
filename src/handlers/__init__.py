from aiogram import Dispatcher, Router
from aiogram.enums import ChatType
from punq import Container

from filters import AdminOnlyFilter, ChatTypeFilter, GroupTypeFilter
from middlewares import AdminAntispamMiddleware
from services.caching import ICache

from .group import router as group_router
from .private import router as private_router
from .private.antibot import router as antibot_router


def registry_admin_routers(dispatcher: Dispatcher, container: Container):
    # Создаем роутер для админов
    only_admin_router = Router(name="admin_router")

    # Регистрируем фильтры: только для приватных чатов и только для админов
    only_admin_router.message.filter(
        ChatTypeFilter(chat_type=[ChatType.PRIVATE]),
        AdminOnlyFilter(),
    )
    only_admin_router.callback_query.filter(
        ChatTypeFilter(chat_type=[ChatType.PRIVATE]),
        AdminOnlyFilter(),
    )

    # Регистрируем антиспам middleware
    cache: ICache = container.resolve(ICache)
    only_admin_router.message.middleware(AdminAntispamMiddleware(cache))

    # Передаем контейнер в контекст через middleware для всех дочерних роутеров
    async def inject_container_to_message(handler, event, data):
        data["container"] = container
        return await handler(event, data)

    async def inject_container_to_callback(handler, event, data):
        data["container"] = container
        return await handler(event, data)

    only_admin_router.message.outer_middleware(inject_container_to_message)
    only_admin_router.callback_query.outer_middleware(inject_container_to_callback)

    # Регистрируем приватный роутер
    only_admin_router.include_router(private_router)

    # Регистрируем роутер для админов
    dispatcher.include_router(only_admin_router)


def registry_public_private_routers(dispatcher: Dispatcher, container: Container):
    # Роутеры для приватных чатов, доступные всем (не только админам)
    public_private_router = Router(name="public_private_router")
    public_private_router.message.filter(ChatTypeFilter(chat_type=[ChatType.PRIVATE]))

    # Передаем контейнер в контекст через middleware
    async def inject_container_to_message(handler, event, data):
        data["container"] = container
        return await handler(event, data)

    async def inject_container_to_callback(handler, event, data):
        data["container"] = container
        return await handler(event, data)

    public_private_router.message.outer_middleware(inject_container_to_message)
    public_private_router.callback_query.outer_middleware(inject_container_to_callback)

    public_private_router.include_router(antibot_router)

    dispatcher.include_router(public_private_router)


def registry_group_routers(dispatcher: Dispatcher):
    # Регистриуем групповой роутер
    public_router = Router(name="public_router")
    public_router.message.filter(GroupTypeFilter())

    public_router.include_router(group_router)

    dispatcher.include_router(public_router)


def registry_routers(dispatcher: Dispatcher, container: Container):
    registry_public_private_routers(dispatcher, container)
    registry_admin_routers(dispatcher, container)
    registry_group_routers(dispatcher)
