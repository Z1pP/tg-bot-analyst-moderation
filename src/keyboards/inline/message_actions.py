from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData


def message_action_ikb() -> types.InlineKeyboardMarkup:
    """Клавиатура с действиями над сообщением."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.Messages.DELETE,
            callback_data=CallbackData.Messages.DELETE_MESSAGE,
        ),
        types.InlineKeyboardButton(
            text=InlineButtons.Messages.REPLY,
            callback_data=CallbackData.Messages.REPLY_MESSAGE,
        ),
    )
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.Messages.CANCEL,
        ),
    )
    return builder.as_markup()


def confirm_delete_ikb() -> types.InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.Messages.CONFIRM_DELETE,
            callback_data=CallbackData.Messages.DELETE_MESSAGE_CONFIRM,
        ),
        types.InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.Messages.DELETE_MESSAGE_CANCEL,
        ),
    )
    return builder.as_markup()


def send_message_ikb() -> types.InlineKeyboardMarkup:
    """Клавиатура с кнопкой отправки сообщения."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.Messages.SEND_MESSAGE,
            callback_data=CallbackData.Messages.SEND_MESSAGE_TO_CHAT,
        ),
        types.InlineKeyboardButton(
            text=InlineButtons.Templates.MENU,
            callback_data=CallbackData.Templates.SHOW_MENU,
        ),
    )
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Menu.SHOW_MENU,
        )
    )
    return builder.as_markup()


def cancel_send_message_ikb() -> types.InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены отправки сообщения."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.Messages.SHOW_MENU,
        )
    )
    return builder.as_markup()


def cancel_reply_ikb() -> types.InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены ответа на сообщение."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.Messages.CANCEL_REPLY,
        )
    )
    return builder.as_markup()


def hide_template_ikb(message_id: int) -> types.InlineKeyboardMarkup:
    """Клавиатура с кнопкой скрытия шаблона."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.Messages.HIDE_TEMPLATE,
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
            text=InlineButtons.Messages.HIDE_ALBUM,
            callback_data=f"hide_album_{message_ids_str}",
        )
    )
    return builder.as_markup()
