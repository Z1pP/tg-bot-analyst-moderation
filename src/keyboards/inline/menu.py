from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData
from constants.enums import UserRole
from constants.i18n import DEFAULT_LANGUAGE
from dto.user import UserDTO


def main_menu_ikb(
    user: Optional[UserDTO] = None,
    user_language: Optional[str] = None,
    admin_tg_id: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """
    Создает inline клавиатуру главного меню администратора с учетом языка пользователя.

    Args:
        user: DTO пользователя или None
        user_language: Код языка пользователя (например, 'ru', 'en')

    Returns:
        InlineKeyboardMarkup: Inline клавиатура главного меню
    """
    if user_language is None:
        user_language = DEFAULT_LANGUAGE

    # users_menu_text = get_text("USERS_MENU", user_language)
    # release_notes_text = get_text("RELEASE_NOTES", user_language)

    builder = InlineKeyboardBuilder()

    # builder.row(
    #     InlineKeyboardButton(
    #         text=users_menu_text,
    #         callback_data=CallbackData.Menu.USERS_MENU,
    #     ),
    #     InlineKeyboardButton(
    #         text=InlineButtons.ChatButtons.CHATS_MANAGEMENT,
    #         callback_data=CallbackData.Menu.CHATS_MENU,
    #     ),
    #     width=2,
    # )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Analytics.MENU,
            callback_data=CallbackData.Analytics.SHOW_MENU,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Moderation.MENU,
            callback_data=CallbackData.Moderation.SHOW_MENU,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Messages.MENU,
            callback_data=CallbackData.Messages.SHOW_MENU,
        ),
        InlineKeyboardButton(
            text=InlineButtons.UserAndChatsSettings.MENU,
            callback_data=CallbackData.UserAndChatsSettings.SHOW_MENU,
        ),
        InlineKeyboardButton(
            text=InlineButtons.BotSettings.MENU,
            callback_data=CallbackData.BotSettings.SHOW_MENU,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Help.MENU,
            callback_data=CallbackData.Help.SHOW_MENU,
        ),
        InlineKeyboardButton(
            text=InlineButtons.News.MENU,
            callback_data=CallbackData.News.SHOW_MENU,
        ),
    )

    if user.role in (UserRole.ROOT, UserRole.DEV):
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.Root.MENU,
                callback_data=CallbackData.Root.SHOW_MENU,
            ),
        )

        builder.adjust(1, 2, 1, 1, 1, 2, 1)
    else:
        builder.adjust(1, 2, 1, 1, 1, 2)

    # # Добавляем кнопку для просмотра логов действий администраторов
    # # (только для авторизованных пользователей)
    # release_admin_id = user.tg_id if user else admin_tg_id
    # if release_admin_id and release_admin_id in RELEASE_NOTES_ADMIN_IDS:
    #     builder.row(
    #         InlineKeyboardButton(
    #             text=Dialog.AdminLogs.ADMIN_LOGS,
    #             callback_data=CallbackData.AdminLogs.MENU,
    #         ),
    #         InlineKeyboardButton(
    #             text=Dialog.Roles.MENU,
    #             callback_data=CallbackData.Role.INPUT_USER_DATA,
    #         ),
    #         width=2,
    #     )

    # builder.row(
    #     InlineKeyboardButton(
    #         text=release_notes_text,
    #         callback_data=CallbackData.ReleaseNotes.MENU,
    #     ),
    # )

    return builder.as_markup()


def close_ikb() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой закрытия уведомления."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.Menu.HIDE_NOTIFICATION,
        )
    )
    return builder.as_markup()
