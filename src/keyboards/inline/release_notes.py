from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData
from constants.i18n import TRANSLATIONS
from models.release_note import ReleaseNote


def release_notes_menu_ikb(
    notes: list[ReleaseNote], page: int, total_pages: int, user_tg_id: str | None = None
) -> InlineKeyboardMarkup:
    """
    Клавиатура меню релизных заметок.

    Args:
        notes: Список релизных заметок
        page: Текущая страница
        total_pages: Всего страниц
        user_tg_id: Telegram ID пользователя для проверки прав доступа
    """
    from constants import RELEASE_NOTES_ADMIN_IDS

    builder = InlineKeyboardBuilder()

    # Список заметок (по 2 в ряд)
    for i in range(0, len(notes), 2):
        row_buttons = []
        note1 = notes[i]
        row_buttons.append(
            InlineKeyboardButton(
                text=note1.title,
                callback_data=f"{CallbackData.ReleaseNotes.PREFIX_SELECT}{note1.id}",
            )
        )
        if i + 1 < len(notes):
            note2 = notes[i + 1]
            row_buttons.append(
                InlineKeyboardButton(
                    text=note2.title,
                    callback_data=f"{CallbackData.ReleaseNotes.PREFIX_SELECT}{note2.id}",
                )
            )
        builder.row(*row_buttons)

    # Пагинация
    if total_pages > 1:
        pagination_buttons = []
        if page > 1:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"{CallbackData.ReleaseNotes.PREFIX_PREV_PAGE}{page - 1}",
                )
            )
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"{page}/{total_pages}",
                callback_data=CallbackData.ReleaseNotes.PAGE_INFO,
            )
        )
        if page < total_pages:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"{CallbackData.ReleaseNotes.PREFIX_NEXT_PAGE}{page + 1}",
                )
            )
        builder.row(*pagination_buttons)

    # Кнопки управления (только для авторизованных пользователей)
    if user_tg_id and user_tg_id in RELEASE_NOTES_ADMIN_IDS:
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.ReleaseNotes.ADD_NOTE,
                callback_data=CallbackData.ReleaseNotes.ADD,
            )
        )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Menu.MAIN_MENU,
        )
    )

    return builder.as_markup()


def release_note_detail_ikb(
    note_id: int, user_tg_id: str | None = None
) -> InlineKeyboardMarkup:
    """
    Клавиатура для просмотра релизной заметки.

    Args:
        note_id: ID заметки
        user_tg_id: Telegram ID пользователя для проверки прав доступа
    """
    from constants import RELEASE_NOTES_ADMIN_IDS

    builder = InlineKeyboardBuilder()

    # Кнопки редактирования, удаления и рассылки (только для авторизованных пользователей)
    if user_tg_id and user_tg_id in RELEASE_NOTES_ADMIN_IDS:
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.ReleaseNotes.EDIT,
                callback_data=f"{CallbackData.ReleaseNotes.EDIT}__{note_id}",
            ),
            InlineKeyboardButton(
                text=InlineButtons.ReleaseNotes.DELETE,
                callback_data=f"{CallbackData.ReleaseNotes.DELETE}__{note_id}",
            ),
            width=2,
        )
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.ReleaseNotes.BROADCAST,
                callback_data=f"{CallbackData.ReleaseNotes.BROADCAST}__{note_id}",
            )
        )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.ReleaseNotes.SHOW_MENU,
        )
    )
    return builder.as_markup()


def edit_release_note_ikb() -> InlineKeyboardMarkup:
    """
    Клавиатура для редактирования релизной заметки.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.ReleaseNotes.EDIT_TITLE,
            callback_data=CallbackData.ReleaseNotes.EDIT_TITLE,
        ),
        InlineKeyboardButton(
            text=InlineButtons.ReleaseNotes.EDIT_CONTENT,
            callback_data=CallbackData.ReleaseNotes.EDIT_CONTENT,
        ),
        width=2,
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.ReleaseNotes.CANCEL_EDIT,
        )
    )
    return builder.as_markup()


def cancel_edit_release_note_ikb() -> InlineKeyboardMarkup:
    """
    Клавиатура для отмены редактирования релизной заметки.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.ReleaseNotes.CANCEL_EDIT,
        )
    )
    return builder.as_markup()


def confirm_delete_release_note_ikb(note_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура для подтверждения удаления релизной заметки.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"{CallbackData.ReleaseNotes.PREFIX_CONFIRM_DELETE}yes__{note_id}",
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=f"{CallbackData.ReleaseNotes.PREFIX_CONFIRM_DELETE}no__{note_id}",
        ),
        width=2,
    )
    return builder.as_markup()


def confirm_broadcast_release_note_ikb(note_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура для подтверждения рассылки релизной заметки.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, разослать",
            callback_data=f"{CallbackData.ReleaseNotes.PREFIX_CONFIRM_BROADCAST}yes__{note_id}",
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=f"{CallbackData.ReleaseNotes.PREFIX_CONFIRM_BROADCAST}no__{note_id}",
        ),
        width=2,
    )
    return builder.as_markup()


def cancel_add_release_note_ikb() -> InlineKeyboardMarkup:
    """
    Клавиатура для отмены добавления релизной заметки (при вводе заголовка).
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.ReleaseNotes.CANCEL_ADD,
        )
    )
    return builder.as_markup()


def change_title_or_cancel_add_ikb() -> InlineKeyboardMarkup:
    """
    Клавиатура для изменения заголовка или отмены при добавлении релизной заметки (при вводе содержимого).
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.ReleaseNotes.EDIT_TITLE,
            callback_data=CallbackData.ReleaseNotes.CHANGE_TITLE_WHILE_ADDING,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.ReleaseNotes.CANCEL_ADD,
        )
    )
    return builder.as_markup()


def select_language_ikb() -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора языка при просмотре заметок.
    """
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки для каждого доступного языка
    for lang_code in TRANSLATIONS.keys():
        lang_name = "Русский" if lang_code == "ru" else "English"
        builder.row(
            InlineKeyboardButton(
                text=lang_name,
                callback_data=f"{CallbackData.ReleaseNotes.PREFIX_SELECT_LANGUAGE}{lang_code}",
            )
        )

    return builder.as_markup()


def select_add_language_ikb() -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора языка при добавлении заметки.
    """
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки для каждого доступного языка
    for lang_code in TRANSLATIONS.keys():
        lang_name = "Русский" if lang_code == "ru" else "English"
        builder.row(
            InlineKeyboardButton(
                text=lang_name,
                callback_data=f"{CallbackData.ReleaseNotes.PREFIX_SELECT_ADD_LANGUAGE}{lang_code}",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.ReleaseNotes.CANCEL_ADD,
        )
    )

    return builder.as_markup()
