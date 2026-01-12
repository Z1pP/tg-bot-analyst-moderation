import logging
from typing import Optional

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from constants.pagination import DEFAULT_PAGE_SIZE
from keyboards.inline.admin_logs import admin_logs_ikb, format_action_type
from repositories import AdminActionLogRepository
from services.time_service import TimeZoneService
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


async def _get_logs_page(
    container: Container, page: int, admin_id: Optional[int] = None
) -> tuple[list, int]:
    """Получает страницу логов."""
    log_repository: AdminActionLogRepository = container.resolve(
        AdminActionLogRepository
    )
    if admin_id:
        return await log_repository.get_logs_by_admin(
            admin_id=admin_id, page=page, limit=DEFAULT_PAGE_SIZE
        )
    else:
        return await log_repository.get_logs_paginated(
            page=page, limit=DEFAULT_PAGE_SIZE
        )


async def _format_logs_message(logs: list, admin_id: Optional[int] = None) -> str:
    """Форматирует список логов в текст сообщения."""
    if not logs:
        if admin_id:
            return "📋 <b>Логи действий администратора</b>\n\nЛоги отсутствуют."
        return "📋 <b>Логи действий всех администраторов</b>\n\nЛоги отсутствуют."

    if admin_id:
        admin_username = (
            logs[0].admin.username
            if logs[0].admin.username
            else f"ID:{logs[0].admin.tg_id}"
        )
        header_text = f"📋 <b>Логи действий администратора @{admin_username}</b>\n"
    else:
        header_text = "📋 <b>Логи действий всех администраторов</b>\n"

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

    return "\n".join(text_parts)


@router.callback_query(F.data.startswith("prev_admin_logs_page__"))
async def prev_admin_logs_page_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик перехода на предыдущую страницу логов."""
    await callback.answer()

    try:
        # Парсим callback_data: prev_admin_logs_page__{page} или prev_admin_logs_page__{page}__{admin_id}
        parts = callback.data.split("__")
        current_page = int(parts[1])
        admin_id = int(parts[2]) if len(parts) > 2 and parts[2] != "None" else None
        prev_page = max(1, current_page - 1)

        logs, total_count = await _get_logs_page(
            container, prev_page, admin_id=admin_id
        )
        text = await _format_logs_message(logs, admin_id=admin_id)

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=text,
            reply_markup=admin_logs_ikb(
                page=prev_page,
                total_count=total_count,
                page_size=DEFAULT_PAGE_SIZE,
                admin_id=admin_id,
            ),
        )
    except Exception as e:
        logger.error(
            "Ошибка при переходе на предыдущую страницу логов: %s", e, exc_info=True
        )
        await callback.answer(Dialog.AdminLogs.ERROR_LOAD_PAGE, show_alert=True)


@router.callback_query(F.data.startswith("next_admin_logs_page__"))
async def next_admin_logs_page_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик перехода на следующую страницу логов."""
    await callback.answer()

    try:
        # Парсим callback_data: next_admin_logs_page__{page} или next_admin_logs_page__{page}__{admin_id}
        parts = callback.data.split("__")
        current_page = int(parts[1])
        admin_id = int(parts[2]) if len(parts) > 2 and parts[2] != "None" else None
        next_page = current_page + 1

        logs, total_count = await _get_logs_page(
            container, next_page, admin_id=admin_id
        )
        if not logs:
            await callback.answer(Dialog.AdminLogs.LAST_PAGE, show_alert=True)
            return

        text = await _format_logs_message(logs, admin_id=admin_id)

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=text,
            reply_markup=admin_logs_ikb(
                page=next_page,
                total_count=total_count,
                page_size=DEFAULT_PAGE_SIZE,
                admin_id=admin_id,
            ),
        )
    except Exception as e:
        logger.error(
            "Ошибка при переходе на следующую страницу логов: %s", e, exc_info=True
        )
        await callback.answer(Dialog.AdminLogs.ERROR_LOAD_PAGE, show_alert=True)


@router.callback_query(F.data == "admin_logs_page_info")
async def admin_logs_page_info_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик информации о странице (не делает ничего, просто отвечает)."""
    await callback.answer()
