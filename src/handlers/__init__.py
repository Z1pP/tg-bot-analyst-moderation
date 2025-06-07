from aiogram import Dispatcher, Router
from aiogram.enums import ChatType

from filters.admin_filter import AdminOnlyFilter
from filters.group_filter import ChatTypeFilter

from .group import router as group_router
from .private import router as private_router


def registry_admin_routers(dispatcher: Dispatcher):
    # Создаем роутер для админов
    admin_router = Router(name="admin_router")

    # Регистрируем фильтры: только для приватных чатов и только для админов
    admin_router.message.filter(
        ChatTypeFilter(chat_type=[ChatType.PRIVATE]),
        AdminOnlyFilter(),
    )

    # Регистрируем приватный роутер
    admin_router.include_router(private_router)

    # Регистрируем роутер для админов
    dispatcher.include_router(admin_router)


def registry_group_routers(dispatcher: Dispatcher):
    # Регистриуем групповой роутер
    dispatcher.include_router(group_router)


def registry_routers(dispatcher: Dispatcher):
    registry_admin_routers(dispatcher)
    registry_group_routers(dispatcher)
