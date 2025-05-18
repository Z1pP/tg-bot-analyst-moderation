from aiogram import Dispatcher, Router
from aiogram.enums import ChatType

from filters.group_filter import ChatTypeFilter
from filters.role_filter import IsAdminFilter

from .group.message_handler import router as message_router

# Роутеры для приватного чата
from .private.avg_messages_count_handler import router as avg_messages_count_router
from .private.commands_handler import router as commands_router
from .private.help_handler import router as help_router
from .private.report_daily_handler import router as report_daily_router
from .private.response_time import router as response_time_router
from .private.start_handler import router as start_router


def registry_admin_routers(dispatcher: Dispatcher):
    # Создаем роутер для админов
    admin_router = Router(name="admin_router")

    # Регистрируем фильтры: только для приватных чатов и только для админов
    admin_router.message.filter(
        ChatTypeFilter(chat_type=[ChatType.PRIVATE]),
        IsAdminFilter(),
    )

    # Регистрируем роутеры
    admin_router.include_router(commands_router)
    admin_router.include_router(report_daily_router)
    admin_router.include_router(avg_messages_count_router)
    admin_router.include_router(start_router)
    admin_router.include_router(help_router)
    admin_router.include_router(response_time_router)

    # Регистрируем роутер для админов
    dispatcher.include_router(admin_router)


def registry_routers(dispatcher: Dispatcher):
    registry_admin_routers(dispatcher)

    # Регистриуем групповой роутер
    dispatcher.include_router(message_router)
