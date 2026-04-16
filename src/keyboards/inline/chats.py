from typing import List, Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData
from constants.pagination import CHATS_PAGE_SIZE
from dto import ChatDTO
from models import ChatSession


def _build_pagination_row(
    page: int,
    total_count: int,
    page_size: int,
    *,
    prev_prefix: str,
    next_prefix: str,
    page_info_callback: str,
) -> List[InlineKeyboardButton]:
    """Строит ряд кнопок пагинации (prev, info, next)."""
    if total_count <= page_size:
        return []
    max_pages = (total_count + page_size - 1) // page_size
    buttons: List[InlineKeyboardButton] = []
    if page > 1:
        buttons.append(
            InlineKeyboardButton(text="◀️", callback_data=f"{prev_prefix}{page}")
        )
    start_item = (page - 1) * page_size + 1
    end_item = min(page * page_size, total_count)
    buttons.append(
        InlineKeyboardButton(
            text=f"{start_item}-{end_item} из {total_count}",
            callback_data=page_info_callback,
        )
    )
    if page < max_pages:
        buttons.append(
            InlineKeyboardButton(text="▶️", callback_data=f"{next_prefix}{page}")
        )
    return buttons


def back_to_chats_menu_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Chat.SHOW_MENU,
        )
    )
    return builder.as_markup()


def back_to_chat_actions_only_ikb() -> InlineKeyboardMarkup:
    """Клавиатура с одной кнопкой «Вернуться» к меню действий чата."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Chat.BACK_TO_CHAT_ACTIONS,
        )
    )
    return builder.as_markup()


def remove_chat_ikb(
    chats: List[ChatSession],
    page: int = 1,
    total_count: int = 0,
    page_size: int = CHATS_PAGE_SIZE,
) -> InlineKeyboardMarkup:
    """Клавиатура для удаления чатов с пагинацией"""
    builder = InlineKeyboardBuilder()

    start_index = (page - 1) * page_size
    for index, chat in enumerate(chats):
        builder.row(
            InlineKeyboardButton(
                text=f"{start_index + index + 1}. Удалить {chat.title[:30]}",
                callback_data=f"{CallbackData.Chat.PREFIX_UNTRACK_CHAT}{chat.id}",
            )
        )

    pagination_buttons = _build_pagination_row(
        page=page,
        total_count=total_count,
        page_size=page_size,
        prev_prefix=CallbackData.Chat.PREFIX_PREV_REMOVE_CHATS_PAGE,
        next_prefix=CallbackData.Chat.PREFIX_NEXT_REMOVE_CHATS_PAGE,
        page_info_callback=CallbackData.Chat.REMOVE_CHATS_PAGE_INFO,
    )
    if pagination_buttons:
        builder.row(*pagination_buttons)

    # Кнопка возврата в меню (в самом низу)
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Chat.SHOW_MENU,
        )
    )

    return builder.as_markup()


def show_tracked_chats_ikb(
    chats: List[ChatDTO],
    page: int = 1,
    total_count: int = 0,
    page_size: int = CHATS_PAGE_SIZE,
    *,
    back_callback: str = CallbackData.Analytics.SHOW_MENU,
    show_management_button: bool = True,
    prev_page_prefix: str = CallbackData.Chat.PREFIX_PREV_CHATS_PAGE,
    next_page_prefix: str = CallbackData.Chat.PREFIX_NEXT_CHATS_PAGE,
) -> InlineKeyboardMarkup:
    """Клавиатура списка чатов с поддержкой пагинации и контекста."""
    builder = InlineKeyboardBuilder()

    # Кнопки чатов
    start_index = (page - 1) * page_size
    for index, chat in enumerate(chats):
        builder.row(
            InlineKeyboardButton(
                text=f"{start_index + index + 1}. {chat.title[:30]}",
                callback_data=f"{CallbackData.Chat.PREFIX_CHAT}{chat.id}",
            )
        )

    pagination_buttons = _build_pagination_row(
        page=page,
        total_count=total_count,
        page_size=page_size,
        prev_prefix=prev_page_prefix,
        next_prefix=next_page_prefix,
        page_info_callback=CallbackData.Chat.CHATS_PAGE_INFO,
    )
    if pagination_buttons:
        builder.row(*pagination_buttons)

    # Кнопка перехода в меню управления чатами
    if show_management_button:
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.Chat.MANAGEMENT,
                callback_data=CallbackData.Chat.SHOW_MENU,
            ),
        )

    # Кнопка возврата в меню (в самом низу)
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=back_callback,
        ),
    )

    return builder.as_markup()


def tracked_chats_with_all_ikb(
    dtos: List[ChatDTO],
    page: int = 1,
    total_count: int = 0,
    page_size: int = CHATS_PAGE_SIZE,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if total_count > 1:
        # Кнопка "Все чаты" первой
        builder.row(
            InlineKeyboardButton(
                text="🌐 Все чаты",
                callback_data=CallbackData.Chat.ALL_CHATS,
            )
        )

    # Кнопки чатов
    start_index = (page - 1) * page_size
    for index, dto in enumerate(dtos):
        builder.row(
            InlineKeyboardButton(
                text=f"{start_index + index + 1}. {dto.title[:30]}",
                callback_data=f"{CallbackData.Chat.PREFIX_CHAT}{dto.id}",
            )
        )

    pagination_buttons = _build_pagination_row(
        page=page,
        total_count=total_count,
        page_size=page_size,
        prev_prefix=CallbackData.Chat.PREFIX_PREV_CHATS_PAGE,
        next_prefix=CallbackData.Chat.PREFIX_NEXT_CHATS_PAGE,
        page_info_callback=CallbackData.Chat.CHATS_PAGE_INFO,
    )
    if pagination_buttons:
        builder.row(*pagination_buttons)

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.Moderation.SHOW_MENU,
        )
    )

    return builder.as_markup()


def template_scope_selector_ikb(chats: List[ChatSession]) -> InlineKeyboardMarkup:
    """Клавиатура для выбора области применения шаблона"""
    kb = InlineKeyboardBuilder()

    kb.button(
        text="🌐 Для всех чатов",
        callback_data=f"{CallbackData.Chat.PREFIX_TEMPLATE_SCOPE}-1",
    )

    # Добавляем доступные чаты
    for chat in chats:
        kb.button(
            text=f"💬 {chat.title[:30]}",
            callback_data=f"{CallbackData.Chat.PREFIX_TEMPLATE_SCOPE}{chat.id}",
        )

    # Формируем сетку 1 кнопка в ряд
    kb.adjust(1)
    return kb.as_markup()


def conf_remove_chat_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Да",
            callback_data=f"{CallbackData.Chat.PREFIX_CONFIRM_REMOVE_CHAT}yes",
        ),
        InlineKeyboardButton(
            text="Нет",
            callback_data=f"{CallbackData.Chat.PREFIX_CONFIRM_REMOVE_CHAT}no",
        ),
        width=2,
    )
    return builder.as_markup()


def hide_notification_ikb() -> InlineKeyboardMarkup:
    """Клавиатура для закрытия уведомления"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.HIDE_NOTIFICATION,
            callback_data=CallbackData.Menu.HIDE_NOTIFICATION,
        )
    )
    return builder.as_markup()


def move_to_chat_analytics_ikb(chat_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для перехода в раздел аналитики чата"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.User.MOVE_TO_ANALYTICS,
            callback_data=f"{CallbackData.Chat.PREFIX_CHAT}{chat_id}",
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.HIDE_NOTIFICATION,
            callback_data=CallbackData.Menu.HIDE_NOTIFICATION,
        ),
        width=1,
    )
    return builder.as_markup()


def select_chat_ikb(
    chats: List[ChatDTO],
    page: int = 1,
    total_count: int = 0,
    page_size: int = CHATS_PAGE_SIZE,
) -> InlineKeyboardMarkup:
    """Клавиатура для выбора чата для отправки сообщения с пагинацией."""
    builder = InlineKeyboardBuilder()

    if total_count > 1:
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.Messages.SEND_TO_ALL_CHATS,
                callback_data=CallbackData.Messages.SELECT_ALL_CHATS,
            ),
        )

    start_index = (page - 1) * page_size
    for index, chat in enumerate(chats):
        builder.row(
            InlineKeyboardButton(
                text=f"{start_index + index + 1}. {chat.title[:30]}",
                callback_data=f"{CallbackData.Messages.PREFIX_SELECT_CHAT}{chat.id}",
            )
        )

    pagination_buttons = _build_pagination_row(
        page=page,
        total_count=total_count,
        page_size=page_size,
        prev_prefix=CallbackData.Messages.PREFIX_PREV_SELECT_CHAT_PAGE,
        next_prefix=CallbackData.Messages.PREFIX_NEXT_SELECT_CHAT_PAGE,
        page_info_callback=CallbackData.Messages.SELECT_CHAT_PAGE_INFO,
    )
    if pagination_buttons:
        builder.row(*pagination_buttons)

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Messages.SHOW_MENU,
        )
    )

    return builder.as_markup()


def chat_actions_ikb() -> InlineKeyboardMarkup:
    """Клавиатура действий с выбранным чатом"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.REPORT_TIME_SETTING,
            callback_data=CallbackData.Chat.REPORT_TIME_SETTING,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Chat.ARCHIVE_CHANNEL_SETTING,
            callback_data=CallbackData.Chat.ARCHIVE_SETTING,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Chat.ANTIBOT_SETTING,
            callback_data=CallbackData.Chat.ANTIBOT_SETTING,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Chat.WELCOME_TEXT_SETTING,
            callback_data=CallbackData.Chat.WELCOME_TEXT_SETTING,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Chat.CHECK_PERMISSIONS,
            callback_data=CallbackData.Chat.CHECK_PERMISSIONS,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Chat.PUNISHMENT_SETTING,
            callback_data=CallbackData.Chat.PUNISHMENT_SETTING,
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Chat.SELECT_CHAT_FOR_SETTINGS,
        ),
    )

    builder.adjust(2, 2, 2, 1)

    return builder.as_markup()


def analytics_chat_actions_ikb() -> InlineKeyboardMarkup:
    """Клавиатура действий для аналитики по чату."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.STATISTICS,
            callback_data=CallbackData.Chat.GET_REPORT,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.GET_DAILY_RATING,
            callback_data=CallbackData.Chat.GET_DAILY_RATING,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.AI_SUMMARY,
            callback_data=CallbackData.Chat.GET_CHAT_SUMMARY_24H,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.SELECT_OTHER_CHAT,
            callback_data=CallbackData.Chat.SELECT_CHAT_FOR_REPORT,
        )
    )

    return builder.as_markup()


def confirm_set_default_punishments_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.CANCEL_SET_DEFAULT,
            callback_data=CallbackData.Chat.CANCEL_SET_DEFAULT,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Chat.CONFIRM_SET_DEFAULT,
            callback_data=CallbackData.Chat.CONFIRM_SET_DEFAULT,
        ),
        width=2,
    )
    return builder.as_markup()


def cancel_welcome_text_setting_ikb() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены для настройки приветственного текста"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Chat.WELCOME_TEXT_SETTING,
        )
    )
    return builder.as_markup()


def antibot_setting_ikb(is_enabled: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура раздела Антибот"""
    builder = InlineKeyboardBuilder()

    toggle_text = (
        InlineButtons.Chat.ANTIBOT_DISABLE
        if is_enabled
        else InlineButtons.Chat.ANTIBOT_ENABLE
    )
    builder.row(
        InlineKeyboardButton(
            text=toggle_text,
            callback_data=CallbackData.Chat.ANTIBOT_TOGGLE,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Chat.WELCOME_TEXT_SETTING,
            callback_data=CallbackData.Chat.WELCOME_TEXT_SETTING,
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Chat.BACK_TO_CHAT_ACTIONS,
        )
    )

    builder.adjust(2, 1)
    return builder.as_markup()


def welcome_text_setting_ikb(
    welcome_text_enabled: bool = False,
    auto_delete_enabled: bool = False,
) -> InlineKeyboardMarkup:
    """Клавиатура раздела Приветственный текст"""
    builder = InlineKeyboardBuilder()

    auto_delete_text = (
        InlineButtons.Chat.AUTO_DELETE_DISABLE
        if auto_delete_enabled
        else InlineButtons.Chat.AUTO_DELETE_ENABLE
    )
    welcome_text_text = (
        InlineButtons.Chat.WELCOME_TEXT_DISABLE
        if welcome_text_enabled
        else InlineButtons.Chat.WELCOME_TEXT_ENABLE
    )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.CHANGE_WELCOME_TEXT,
            callback_data=CallbackData.Chat.CHANGE_WELCOME_TEXT,
        ),
        InlineKeyboardButton(
            text=welcome_text_text,
            callback_data=CallbackData.Chat.WELCOME_TEXT_TOGGLE,
        ),
        InlineKeyboardButton(
            text=auto_delete_text,
            callback_data=CallbackData.Chat.AUTO_DELETE_TOGGLE,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Chat.ANTIBOT_SETTING,
            callback_data=CallbackData.Chat.ANTIBOT_SETTING,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Chat.BACK_TO_CHAT_ACTIONS,
        ),
    )

    builder.adjust(1, 2, 1, 1)

    return builder.as_markup()


def rating_report_ikb(
    back_callback: str = CallbackData.Chat.BACK_TO_ANALYTICS_CHAT_ACTIONS,
) -> InlineKeyboardMarkup:
    """Клавиатура для отчета по рейтингу"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=back_callback,
        )
    )

    return builder.as_markup()


def not_tracked_chats_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.MANAGEMENT,
            callback_data=CallbackData.Chat.MANAGEMENT,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Chat.SHOW_MENU,
        ),
        width=1,
    )
    return builder.as_markup()


def chats_menu_ikb(
    has_tracked_chats: bool = True,
    callback_data: str = CallbackData.Chat.BACK_TO_MAIN_MENU_FROM_CHATS,
) -> InlineKeyboardMarkup:
    "Клавиатура меню чатов"
    builder = InlineKeyboardBuilder()

    if has_tracked_chats:
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.Chat.SELECT_CHAT,
                callback_data=CallbackData.Chat.SELECT_CHAT_FOR_SETTINGS,
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.ADD,
            callback_data=CallbackData.Chat.ADD,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Chat.REMOVE,
            callback_data=CallbackData.Chat.REMOVE,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=callback_data,
        ),
    )

    if has_tracked_chats:
        builder.adjust(1, 2, 1)
    else:
        builder.adjust(2, 1)

    return builder.as_markup()


def summary_type_ikb(
    back_callback: str = CallbackData.Chat.BACK_TO_CHAT_ACTIONS,
) -> InlineKeyboardMarkup:
    """Клавиатура выбора типа сводки"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.SUMMARY_SHORT,
            callback_data=f"{CallbackData.Chat.PREFIX_CHAT_SUMMARY_TYPE}short",
        ),
        InlineKeyboardButton(
            text=InlineButtons.Chat.SUMMARY_FULL,
            callback_data=f"{CallbackData.Chat.PREFIX_CHAT_SUMMARY_TYPE}full",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=back_callback,
        )
    )

    return builder.as_markup()


def archive_channel_setting_ikb(
    archive_chat: Optional[ChatSession] = None,
    invite_link: Optional[str] = None,
    schedule_enabled: Optional[bool] = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if archive_chat:
        # Используем invite ссылку, если она предоставлена, иначе fallback на прямой URL
        if invite_link:
            url = invite_link
        else:
            url = f"https://t.me/c/{archive_chat.chat_id}/1"

        title = archive_chat.title or "Архивный чат"
        builder.row(
            InlineKeyboardButton(
                text=f"💬 {title[:15]}...",
                url=url,
            ),
            InlineKeyboardButton(
                text=InlineButtons.Chat.ARCHIVE_CHANNEL_REBIND,
                callback_data=CallbackData.Chat.ARCHIVE_BIND_INSTRUCTION,
            ),
        )

        if schedule_enabled is not None:
            toggle_text = (
                InlineButtons.Chat.ARCHIVE_SCHEDULE_DISABLE
                if schedule_enabled
                else InlineButtons.Chat.ARCHIVE_SCHEDULE_ENABLE
            )

            builder.row(
                InlineKeyboardButton(
                    text=toggle_text,
                    callback_data=CallbackData.Chat.ARCHIVE_TOGGLE_SCHEDULE,
                ),
            )

        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.Chat.ARCHIVE_TIME_SETTING,
                callback_data=CallbackData.Chat.ARCHIVE_TIME_SETTING,
            ),
        )

        builder.adjust(1, 2, 1)

    else:
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.Chat.ARCHIVE_CHANNEL_BIND,
                callback_data=CallbackData.Chat.ARCHIVE_BIND_INSTRUCTION,
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Chat.BACK_TO_CHAT_ACTIONS,
        )
    )

    return builder.as_markup()


def archive_bind_instruction_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Chat.ARCHIVE_SETTING,
        )
    )
    return builder.as_markup()


def cancel_archive_time_setting_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Chat.ARCHIVE_SETTING,
        )
    )
    return builder.as_markup()


def time_report_settings_ikb() -> InlineKeyboardMarkup:
    """Клавиатура меню выбора параметра для настройки времени сбора данных"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.CHANGE_WORK_START,
            callback_data=CallbackData.Chat.CHANGE_WORK_START,
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.CHANGE_WORK_END,
            callback_data=CallbackData.Chat.CHANGE_WORK_END,
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.CHANGE_TOLERANCE,
            callback_data=CallbackData.Chat.CHANGE_TOLERANCE,
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.CHANGE_BREAKS_TIME,
            callback_data=CallbackData.Chat.CHANGE_BREAKS_TIME,
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Chat.CANCEL_TIME_SETTING,
        ),
    )

    builder.adjust(2, 1, 1, 1)

    return builder.as_markup()


def cancel_work_hours_setting_ikb() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены для настройки времени сбора данных"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.Chat.REPORT_TIME_SETTING,
        )
    )
    return builder.as_markup()
