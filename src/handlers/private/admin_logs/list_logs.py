import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from constants.callback import CallbackData
from constants.pagination import DEFAULT_PAGE_SIZE
from container import container
from keyboards.inline.admin_logs import (
    admin_logs_ikb,
    admin_select_ikb,
    format_action_type,
)
from keyboards.inline.menu import admin_menu_ikb
from repositories import AdminActionLogRepository
from services.time_service import TimeZoneService
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.AdminLogs.MENU)
async def admin_logs_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Обработчик просмотра логов действий администраторов - показывает список администраторов."""
    await callback.answer()

    try:
        log_repository: AdminActionLogRepository = container.resolve(
            AdminActionLogRepository
        )

        # Получаем список администраторов с логами
        admins = await log_repository.get_admins_with_logs()

        # Формируем текст сообщения
        if not admins:
            text = f"{Dialog.AdminLogs.ADMIN_LOGS_TITLE}\n\n{Dialog.AdminLogs.NO_LOGS}"
        else:
            text = Dialog.AdminLogs.SELECT_ADMIN

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=text,
            reply_markup=admin_select_ikb(admins),
        )

    except Exception as e:
        logger.error(
            "Ошибка при получении списка администраторов: %s", e, exc_info=True
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.AdminLogs.ERROR_GET_ADMINS,
            reply_markup=admin_menu_ikb(),
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
            header_text = Dialog.AdminLogs.ALL_ADMINS_LOGS
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
                header_text = Dialog.AdminLogs.ADMIN_LOGS_FORMAT.format(
                    username=admin_username
                )
            else:
                admin_username = "неизвестен"
                header_text = Dialog.AdminLogs.ADMIN_LOGS_FORMAT.format(
                    username=admin_username
                )

        if not logs:
            await callback.message.edit_text(
                f"{header_text}\n{Dialog.AdminLogs.NO_LOGS}",
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
        await callback.answer(Dialog.AdminLogs.ERROR_GET_LOGS, show_alert=True)


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
                f"{Dialog.AdminLogs.ADMIN_LOGS_TITLE}\n\n{Dialog.AdminLogs.NO_LOGS}",
            )
            return

        # Формируем текст сообщения
        text = Dialog.AdminLogs.SELECT_ADMIN

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
            Dialog.AdminLogs.ERROR_GET_ADMINS_ALERT,
            show_alert=True,
        )
