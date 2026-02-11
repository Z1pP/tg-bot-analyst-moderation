"""Пакет хендлеров для амнистии пользователей.

Содержит логику для снятия ограничений (бан, мут) и отмены предупреждений
в одном или нескольких чатах.
"""

from aiogram import Router

from . import base

router = Router(name="amnesty_router")
router.include_router(base.router)
