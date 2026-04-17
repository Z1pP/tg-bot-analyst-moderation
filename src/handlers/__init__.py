from aiogram import Dispatcher, Router
from aiogram.enums import ChatType
from punq import Container

from filters import AdminOnlyFilter, ChatTypeFilter, GroupTypeFilter
from middlewares import AdminAntispamMiddleware
from services.caching import ICache

from .group import router as group_router
from .private import router as private_router


def _make_inject_container_middleware(container: Container):
    """Фабрика middleware: подставляет container в data для handler."""

    async def middleware(handler, event, data):
        data["container"] = container
        return await handler(event, data)

    return middleware


def registry_admin_routers(dispatcher: Dispatcher, container: Container) -> None:
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
    inject_container = _make_inject_container_middleware(container)
    only_admin_router.message.outer_middleware(inject_container)
    only_admin_router.callback_query.outer_middleware(inject_container)
    only_admin_router.inline_query.outer_middleware(inject_container)

    # Регистрируем приватный роутер
    only_admin_router.include_router(private_router)

    # Регистрируем роутер для админов
    dispatcher.include_router(only_admin_router)


def registry_group_routers(dispatcher: Dispatcher, container: Container) -> None:
    # Регистриуем групповой роутер
    public_router = Router(name="public_router")
    public_router.message.filter(GroupTypeFilter())

    # Передаем контейнер в контекст через middleware для всех групповых обновлений
    inject_container = _make_inject_container_middleware(container)
    public_router.message.outer_middleware(inject_container)
    public_router.callback_query.outer_middleware(inject_container)
    public_router.message_reaction.outer_middleware(inject_container)
    public_router.chat_member.outer_middleware(inject_container)
    public_router.inline_query.outer_middleware(inject_container)

    public_router.include_router(group_router)

    dispatcher.include_router(public_router)


def registry_routers(dispatcher: Dispatcher, container: Container) -> None:
    registry_admin_routers(dispatcher, container)
    registry_group_routers(dispatcher, container)
