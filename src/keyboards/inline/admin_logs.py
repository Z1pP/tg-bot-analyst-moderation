from typing import List, Tuple

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData
from constants.enums import AdminActionType
from constants.pagination import DEFAULT_PAGE_SIZE
from models import AdminActionLog


def admin_logs_ikb(
    logs: List[AdminActionLog],
    page: int = 1,
    total_count: int = 0,
    page_size: int = DEFAULT_PAGE_SIZE,
    admin_id: int = None,
) -> InlineKeyboardMarkup:
    """Клавиатура для списка логов действий администраторов."""
    builder = InlineKeyboardBuilder()

    # Пагинация (только если больше одной страницы)
    if total_count > page_size:
        max_pages = (total_count + page_size - 1) // page_size
        pagination_buttons = []

        # Кнопка "Назад"
        if page > 1:
            callback_data = f"prev_admin_logs_page__{page}"
            if admin_id:
                callback_data += f"__{admin_id}"
            pagination_buttons.append(
                InlineKeyboardButton(text="◀️", callback_data=callback_data)
            )

        # Информация о странице
        start_item = (page - 1) * page_size + 1
        end_item = min(page * page_size, total_count)
        callback_data = "admin_logs_page_info"
        if admin_id:
            callback_data += f"__{admin_id}"
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"{start_item}-{end_item} из {total_count}",
                callback_data=callback_data,
            )
        )

        # Кнопка "Вперед"
        if page < max_pages:
            callback_data = f"next_admin_logs_page__{page}"
            if admin_id:
                callback_data += f"__{admin_id}"
            pagination_buttons.append(
                InlineKeyboardButton(text="▶️", callback_data=callback_data)
            )

        if pagination_buttons:
            builder.row(*pagination_buttons)

    # Кнопка "Выбрать администратора" (только если есть логи)
    if logs:
        builder.row(
            InlineKeyboardButton(
                text="🔄 Выбрать администратора",
                callback_data="admin_logs_select_admin",
            )
        )

    # Кнопка "Скрыть"
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.HIDE,
            callback_data=CallbackData.AdminLogs.HIDE_LOGS,
        )
    )

    return builder.as_markup()


def admin_select_ikb(admins: List[Tuple[int, str, str]]) -> InlineKeyboardMarkup:
    """Клавиатура для выбора администратора для просмотра логов."""
    builder = InlineKeyboardBuilder()

    # Кнопка "Все администраторы"
    builder.row(
        InlineKeyboardButton(
            text="📋 Все администраторы",
            callback_data="admin_logs__all",
        )
    )

    # Кнопки для каждого администратора
    for admin_id, username, tg_id in admins:
        builder.row(
            InlineKeyboardButton(
                text=f"👤 @{username}",
                callback_data=f"admin_logs__{admin_id}",
            )
        )

    # Кнопка "Скрыть"
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.HIDE,
            callback_data=CallbackData.AdminLogs.HIDE_LOGS,
        )
    )

    return builder.as_markup()


def format_action_type(action_type: str | AdminActionType) -> str:
    """Форматирует тип действия для отображения."""
    # Если передан enum, получаем его значение
    if isinstance(action_type, AdminActionType):
        action_type_str = action_type.value
    else:
        action_type_str = action_type

    action_names = {
        "report_user": "📊 Отчет по пользователю",
        "report_chat": "📊 Отчет по чату",
        "report_all_users": "📊 Отчет по всем пользователям",
        "add_template": "➕ Добавление шаблона",
        "delete_template": "🗑 Удаление шаблона",
        "add_category": "➕ Добавление категории",
        "delete_category": "🗑 Удаление категории",
        "send_message": "📤 Отправка сообщения",
        "delete_message": "🗑 Удаление сообщения",
        "reply_message": "💬 Ответ на сообщение",
    }
    return action_names.get(action_type_str, action_type_str)
