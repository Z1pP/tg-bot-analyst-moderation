from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import Dialog, InlineButtons
from constants.callback import CallbackData
from constants.pagination import USERS_PAGE_SIZE
from dto.user import UserDTO


def users_menu_ikb(has_tracked_users: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура меню пользователей"""
    builder = InlineKeyboardBuilder()

    if has_tracked_users:
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.UserButtons.SHOW_TRACKED_USERS_LIST,
                callback_data=CallbackData.User.SHOW_TRACKED_USERS_LIST,
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.ADD,
            callback_data=CallbackData.User.ADD,
        ),
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.REMOVE,
            callback_data=CallbackData.User.REMOVE,
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.COME_BACK,
            callback_data=CallbackData.User.BACK_TO_MAIN_MENU_FROM_USERS,
        ),
    )

    if has_tracked_users:
        builder.adjust(1, 2, 1)
    else:
        builder.adjust(2, 1)

    return builder.as_markup()


def move_to_analytics_ikb(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для перехода в раздел аналитики или назад в меню пользователей"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.MOVE_TO_ANALYTICS,
            callback_data=CallbackData.User.PREFIX_USER + str(user_id),
        ),
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.HIDE_NOTIFICATION,
            callback_data=CallbackData.Menu.HIDE_NOTIFICATION,
        ),
        width=1,
    )
    return builder.as_markup()


def hide_notification_ikb() -> InlineKeyboardMarkup:
    """Клавиатура для закрытия уведомления"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.HIDE_NOTIFICATION,
            callback_data=CallbackData.Menu.HIDE_NOTIFICATION,
        )
    )

    return builder.as_markup()


def back_to_users_menu_ikb() -> InlineKeyboardMarkup:
    """Клавиатура для возврата в меню пользователей"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.COME_BACK,
            callback_data=CallbackData.User.SELECT_USER,
        )
    )
    return builder.as_markup()


def remove_user_inline_kb(
    users: List[UserDTO],
    page: int = 1,
    total_count: int = 0,
    page_size: int = USERS_PAGE_SIZE,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Кнопки удаления пользователей
    start_index = (page - 1) * page_size
    for index, user in enumerate(users):
        builder.row(
            InlineKeyboardButton(
                text=f"{start_index + index + 1}. Удалить {user.username}",
                callback_data=f"{CallbackData.User.PREFIX_REMOVE_USER}{user.id}",
            )
        )

    # Пагинация (только если больше одной страницы)
    if total_count > page_size:
        max_pages = (total_count + page_size - 1) // page_size
        pagination_buttons = []

        # Кнопка "Назад"
        if page > 1:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="◀️",
                    callback_data=f"{CallbackData.User.PREFIX_PREV_REMOVE_USERS_PAGE}{page}",
                )
            )

        # Информация о странице
        start_item = (page - 1) * page_size + 1
        end_item = min(page * page_size, total_count)
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"{start_item}-{end_item} из {total_count}",
                callback_data=CallbackData.User.REMOVE_USERS_PAGE_INFO,
            )
        )

        # Кнопка "Вперед"
        if page < max_pages:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="▶️",
                    callback_data=f"{CallbackData.User.PREFIX_NEXT_REMOVE_USERS_PAGE}{page}",
                )
            )

        if pagination_buttons:
            builder.row(*pagination_buttons)

    # Кнопка возврата в меню (в самом низу)
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.BACK_TO_USERS_MENU,
            callback_data=CallbackData.User.SELECT_USER,
        )
    )

    return builder.as_markup()


def conf_remove_user_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Да",
            callback_data=f"{CallbackData.User.PREFIX_CONFIRM_REMOVE_USER}yes",
        ),
        InlineKeyboardButton(
            text="Нет",
            callback_data=f"{CallbackData.User.PREFIX_CONFIRM_REMOVE_USER}no",
        ),
        width=2,
    )
    return builder.as_markup()


def user_actions_ikb() -> InlineKeyboardMarkup:
    """Клавиатура действий с выбранным пользователем"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=Dialog.Report.GET_REPORT,
            callback_data=CallbackData.Report.GET_USER_REPORT,
        ),
        # InlineKeyboardButton(
        #     text=Dialog.User.SELECT_USER,
        #     callback_data=CallbackData.User.SHOW_TRACKED_USERS_LIST,
        # ),
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.BACK_TO_USERS_MENU,
            callback_data=CallbackData.User.SELECT_USER,
        ),
        width=1,
    )

    return builder.as_markup()


def all_users_actions_ikb() -> InlineKeyboardMarkup:
    """Клавиатура действий со всеми пользователями"""

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=Dialog.Report.GET_REPORT,
            callback_data=CallbackData.Report.GET_ALL_USERS_REPORT,
        ),
        # InlineKeyboardButton(
        #     text=Dialog.User.SELECT_USER,
        #     callback_data=CallbackData.User.SHOW_TRACKED_USERS_LIST,
        # ),
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.BACK_TO_USERS_MENU,
            callback_data=CallbackData.User.SELECT_USER,
        ),
        width=1,
    )

    return builder.as_markup()
