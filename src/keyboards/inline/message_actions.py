from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons


def message_action_ikb() -> types.InlineKeyboardMarkup:
    """Клавиатура с действиями над сообщением."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.MessageButtons.DELETE,
            callback_data="delete_message",
        ),
        types.InlineKeyboardButton(
            text=InlineButtons.MessageButtons.REPLY,
            callback_data="reply_message",
        ),
    )
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.MessageButtons.CANCEL,
            callback_data="cancel",
        ),
    )
    return builder.as_markup()


def confirm_delete_ikb() -> types.InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.MessageButtons.CONFIRM_DELETE,
            callback_data="delete_message_confirm",
        ),
        types.InlineKeyboardButton(
            text=InlineButtons.MessageButtons.CANCEL,
            callback_data="delete_message_cancel",
        ),
    )
    return builder.as_markup()


def send_message_ikb() -> types.InlineKeyboardMarkup:
    """Клавиатура с кнопкой отправки сообщения."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.MessageButtons.SEND_MESSAGE,
            callback_data="send_message_to_chat",
        ),
        types.InlineKeyboardButton(
            text=InlineButtons.MessageButtons.TEMPLATES_MENU,
            callback_data="templates_menu",
        ),
    )
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.UserButtons.COME_BACK,
            callback_data="back_to_main_menu_from_message_management",
        )
    )
    return builder.as_markup()


def cancel_send_message_ikb() -> types.InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены отправки сообщения."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.MessageButtons.CANCEL,
            callback_data="message_management_menu",
        )
    )
    return builder.as_markup()


def cancel_reply_ikb() -> types.InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены ответа на сообщение."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.MessageButtons.CANCEL,
            callback_data="cancel_reply_message",
        )
    )
    return builder.as_markup()


def hide_template_ikb(message_id: int) -> types.InlineKeyboardMarkup:
    """Клавиатура с кнопкой скрытия шаблона."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.MessageButtons.HIDE_TEMPLATE,
            callback_data=f"hide_template_{message_id}",
        )
    )
    return builder.as_markup()


def hide_album_ikb(message_ids: list[int]) -> types.InlineKeyboardMarkup:
    """Клавиатура с кнопкой скрытия альбома шаблонов."""
    builder = InlineKeyboardBuilder()
    # Сохраняем ID всех сообщений через запятую
    message_ids_str = ",".join(map(str, message_ids))
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.MessageButtons.HIDE_ALBUM,
            callback_data=f"hide_album_{message_ids_str}",
        )
    )
    return builder.as_markup()
