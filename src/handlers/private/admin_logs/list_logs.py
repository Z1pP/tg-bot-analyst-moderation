import logging

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from constants.pagination import DEFAULT_PAGE_SIZE
from container import container
from keyboards.inline.admin_logs import (
    admin_logs_ikb,
    admin_select_ikb,
    format_action_type,
)
from keyboards.reply.menu import admin_menu_kb
from repositories import AdminActionLogRepository
from services.time_service import TimeZoneService

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(Command("logs"))
async def admin_logs_handler(message: types.Message, state: FSMContext) -> None:
    """Обработчик просмотра логов действий администраторов - показывает список администраторов."""
    try:
        log_repository: AdminActionLogRepository = container.resolve(
            AdminActionLogRepository
        )

        # Получаем список администраторов с логами
        admins = await log_repository.get_admins_with_logs()

        if not admins:
            await message.answer(
                "📋 Логи действий администраторов\n\nЛоги отсутствуют.",
                reply_markup=admin_menu_kb(),
            )
            return

        # Формируем текст сообщения
        text = "📋 <b>Выберите администратора для просмотра логов</b>\n\n"
        text += "Или выберите <b>Все администраторы</b> для просмотра всех логов."

        await message.answer(
            text,
            reply_markup=admin_select_ikb(admins),
        )

    except Exception as e:
        logger.error(
            "Ошибка при получении списка администраторов: %s", e, exc_info=True
        )
        await message.answer(
            "⚠️ Произошла ошибка при получении списка администраторов.",
            reply_markup=admin_menu_kb(),
        )


@router.callback_query(lambda c: c.data.startswith("admin_logs__"))
async def admin_logs_select_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик выбора администратора для просмотра логов."""
    await callback.answer()

    try:
        log_repository: AdminActionLogRepository = container.resolve(
            AdminActionLogRepository
        )

        # Парсим callback_data: admin_logs__{admin_id} или admin_logs__all
        parts = callback.data.split("__")
        admin_id_str = parts[1] if len(parts) > 1 else None

        if admin_id_str == "all":
            # Показываем все логи
            admin_id = None
            logs, total_count = await log_repository.get_logs_paginated(
                page=1, limit=DEFAULT_PAGE_SIZE
            )
            header_text = "📋 <b>Логи действий всех администраторов</b>\n"
        else:
            # Показываем логи конкретного администратора
            admin_id = int(admin_id_str)
            logs, total_count = await log_repository.get_logs_by_admin(
                admin_id=admin_id, page=1, limit=DEFAULT_PAGE_SIZE
            )
            # Получаем информацию об администраторе
            if logs:
                admin_username = (
                    logs[0].admin.username
                    if logs[0].admin.username
                    else f"ID:{logs[0].admin.tg_id}"
                )
                header_text = (
                    f"📋 <b>Логи действий администратора @{admin_username}</b>\n"
                )
            else:
                admin_username = "неизвестен"
                header_text = (
                    f"📋 <b>Логи действий администратора @{admin_username}</b>\n"
                )

        if not logs:
            await callback.message.edit_text(
                f"{header_text}\nЛоги отсутствуют.",
                reply_markup=admin_logs_ikb(
                    logs=logs,
                    page=1,
                    total_count=total_count,
                    page_size=DEFAULT_PAGE_SIZE,
                    admin_id=admin_id,
                ),
            )
            return

        # Формируем текст сообщения
        text_parts = [header_text]
        for log in logs:
            admin_username = (
                log.admin.username if log.admin.username else f"ID:{log.admin.tg_id}"
            )
            action_name = format_action_type(log.action_type)
            local_time = TimeZoneService.convert_to_local_time(log.created_at)
            time_str = local_time.strftime("%d.%m.%Y %H:%M")
            text_parts.append(
                f"• {action_name}\n  Админ: @{admin_username}\n  Дата: {time_str}"
            )
            # Добавляем детали, если они есть
            if log.details:
                text_parts.append(f"  {log.details}")
            text_parts.append("")  # Пустая строка между записями

        text = "\n".join(text_parts)

        await callback.message.edit_text(
            text,
            reply_markup=admin_logs_ikb(
                logs=logs,
                page=1,
                total_count=total_count,
                page_size=DEFAULT_PAGE_SIZE,
                admin_id=admin_id,
            ),
        )

    except Exception as e:
        logger.error("Ошибка при получении логов администратора: %s", e, exc_info=True)
        await callback.answer("⚠️ Произошла ошибка при получении логов", show_alert=True)


@router.callback_query(F.data == "admin_logs_select_admin")
async def admin_logs_select_admin_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик возврата к выбору администратора."""
    await callback.answer()

    try:
        log_repository: AdminActionLogRepository = container.resolve(
            AdminActionLogRepository
        )

        # Получаем список администраторов с логами
        admins = await log_repository.get_admins_with_logs()

        if not admins:
            await callback.message.edit_text(
                "📋 Логи действий администраторов\n\nЛоги отсутствуют.",
            )
            return

        # Формируем текст сообщения
        text = "📋 <b>Выберите администратора для просмотра логов</b>\n\n"
        text += "Или выберите <b>Все администраторы</b> для просмотра всех логов."

        from keyboards.inline.admin_logs import admin_select_ikb

        await callback.message.edit_text(
            text,
            reply_markup=admin_select_ikb(admins),
        )

    except Exception as e:
        logger.error(
            "Ошибка при получении списка администраторов: %s", e, exc_info=True
        )
        await callback.answer(
            "⚠️ Произошла ошибка при получении списка администраторов",
            show_alert=True,
        )
