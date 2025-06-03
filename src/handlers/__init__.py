from aiogram import Dispatcher, Router
from aiogram.enums import ChatType

from filters.admin_filter import AdminOnlyFilter
from filters.group_filter import ChatTypeFilter

from .group.message_handler import router as message_router
from .private.commands_handler import router as commands_router
from .private.help_handler import router as help_router
from .private.menu_handler import router as menu_router
from .private.moderators_list_handler import router as moderators_list_router

# Роутеры для приватного чата
from .private.reports.full_report_handler import router as full_report_router
from .private.reports.report_response_time_handler import router as response_time_router
from .private.start_handler import router as start_router
from .private.time_router import router as time_router


def registry_admin_routers(dispatcher: Dispatcher):
    # Создаем роутер для админов
    admin_router = Router(name="admin_router")

    # Регистрируем фильтры: только для приватных чатов и только для админов
    admin_router.message.filter(
        ChatTypeFilter(chat_type=[ChatType.PRIVATE]),
        AdminOnlyFilter(),
    )

    # Регистрируем роутеры
    admin_router.include_router(commands_router)
    admin_router.include_router(menu_router)
    admin_router.include_router(start_router)
    admin_router.include_router(help_router)
    admin_router.include_router(response_time_router)
    admin_router.include_router(moderators_list_router)
    admin_router.include_router(full_report_router)
    admin_router.include_router(time_router)

    # Регистрируем роутер для админов
    dispatcher.include_router(admin_router)


def registry_group_routers(dispatcher: Dispatcher):
    # Регистриуем групповой роутер
    group_router = Router(name="group_router")

    group_router.include_router(message_router)

    dispatcher.include_router(group_router)


def registry_routers(dispatcher: Dispatcher):
    registry_admin_routers(dispatcher)

    # Регистриуем групповой роутер
    registry_group_routers(dispatcher)
