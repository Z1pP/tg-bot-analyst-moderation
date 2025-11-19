import logging
import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import Dialog
from constants.callback import CallbackData
from constants.i18n import DEFAULT_LANGUAGE
from container import container
from keyboards.inline.release_notes import (
    cancel_edit_release_note_ikb,
    edit_release_note_ikb,
    release_note_detail_ikb,
    release_notes_menu_ikb,
)
from services.release_note_service import ReleaseNoteService
from services.user import UserService
from states.release_notes import ReleaseNotesStateManager
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith(f"{CallbackData.ReleaseNotes.EDIT}__"))
async def edit_note_start_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала редактирования релизной заметки"""
    from constants import RELEASE_NOTES_ADMIN_IDS

    await callback.answer()

    # Проверка прав доступа
    user_tg_id = str(callback.from_user.id)
    if user_tg_id not in RELEASE_NOTES_ADMIN_IDS:
        await callback.answer(
            "У вас нет прав для редактирования заметок", show_alert=True
        )
        return

    note_id = int(callback.data.split("__")[1])

    release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)
    note = await release_note_service.get_note_by_id(note_id)

    if not note:
        await callback.answer(Dialog.ReleaseNotes.NOTE_NOT_FOUND, show_alert=True)
        return

    # Сохраняем данные заметки
    await state.update_data(
        edit_note_id=note_id,
        original_title=note.title,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ReleaseNotes.EDIT_NOTE.format(title=note.title),
        reply_markup=edit_release_note_ikb(),
    )

    await log_and_set_state(
        callback.message,
        state,
        ReleaseNotesStateManager.editing_note,
    )


@router.callback_query(
    F.data == CallbackData.ReleaseNotes.EDIT_TITLE,
    ReleaseNotesStateManager.editing_note,
)
async def edit_title_start_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала редактирования заголовка"""
    await callback.answer()

    await state.update_data(active_message_id=callback.message.message_id)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ReleaseNotes.EDIT_TITLE_INPUT,
        reply_markup=cancel_edit_release_note_ikb(),
    )

    await log_and_set_state(
        callback.message,
        state,
        ReleaseNotesStateManager.editing_title,
    )


@router.message(ReleaseNotesStateManager.editing_title)
async def process_edit_title_handler(message: Message, state: FSMContext) -> None:
    """Обработчик получения нового заголовка"""
    from constants import RELEASE_NOTES_ADMIN_IDS

    # Проверка прав доступа
    user_tg_id = str(message.from_user.id)
    if user_tg_id not in RELEASE_NOTES_ADMIN_IDS:
        await message.reply("У вас нет прав для редактирования заметок")
        await state.clear()
        return

    data = await state.get_data()
    note_id = data.get("edit_note_id")

    if not note_id:
        await message.reply(Dialog.ReleaseNotes.NOTE_NOT_FOUND)
        return

    new_title = message.text.strip()

    if not new_title or len(new_title) < 3:
        await message.reply("❗Заголовок должен содержать минимум 3 символа.")
        return

    old_title = data.get("original_title", "неизвестно")

    release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)
    success = await release_note_service.update_note_title(note_id, new_title)

    if not success:
        await message.reply(Dialog.ReleaseNotes.ERROR_UPDATE_TITLE)
        return

    await message.delete()

    update_message = Dialog.ReleaseNotes.TITLE_UPDATED.format(
        old_title=old_title, new_title=new_title
    )

    # Возвращаемся к меню релизных заметок
    user_service: UserService = container.resolve(UserService)
    db_user = await user_service.get_user(tg_id=str(message.from_user.id))
    user_language = (
        db_user.language if db_user and db_user.language else DEFAULT_LANGUAGE
    )

    page = 1
    limit = 10
    offset = (page - 1) * limit

    notes = await release_note_service.get_notes(user_language, limit, offset)
    total_count = await release_note_service.count_notes(user_language)
    total_pages = math.ceil(total_count / limit)

    active_message_id = data.get("active_message_id")
    if active_message_id:
        try:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=f"{update_message}\n\n{Dialog.ReleaseNotes.RELEASE_NOTES_MENU}",
                reply_markup=release_notes_menu_ikb(notes, page, total_pages),
            )
            await log_and_set_state(
                message,
                state,
                ReleaseNotesStateManager.menu,
            )
        except Exception as e:
            logger.error("Ошибка при возврате к меню: %s", e, exc_info=True)
            await message.reply(update_message)
    else:
        await message.reply(update_message)


@router.callback_query(
    F.data == CallbackData.ReleaseNotes.EDIT_CONTENT,
    ReleaseNotesStateManager.editing_note,
)
async def edit_content_start_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик начала редактирования содержимого"""
    await callback.answer()

    await state.update_data(active_message_id=callback.message.message_id)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ReleaseNotes.EDIT_CONTENT_INPUT,
        reply_markup=cancel_edit_release_note_ikb(),
    )

    await log_and_set_state(
        callback.message,
        state,
        ReleaseNotesStateManager.editing_content,
    )


@router.message(ReleaseNotesStateManager.editing_content)
async def process_edit_content_handler(message: Message, state: FSMContext) -> None:
    """Обработчик получения нового содержимого"""
    from constants import RELEASE_NOTES_ADMIN_IDS

    # Проверка прав доступа
    user_tg_id = str(message.from_user.id)
    if user_tg_id not in RELEASE_NOTES_ADMIN_IDS:
        await message.reply("У вас нет прав для редактирования заметок")
        await state.clear()
        return

    data = await state.get_data()
    note_id = data.get("edit_note_id")

    if not note_id:
        await message.reply(Dialog.ReleaseNotes.NOTE_NOT_FOUND)
        return

    new_content = message.text.strip()

    if not new_content:
        await message.reply("❗Содержимое не может быть пустым.")
        return

    release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)
    success = await release_note_service.update_note_content(note_id, new_content)

    if not success:
        await message.reply(Dialog.ReleaseNotes.ERROR_UPDATE_CONTENT)
        return

    await message.delete()

    update_message = Dialog.ReleaseNotes.CONTENT_UPDATED

    # Возвращаемся к меню релизных заметок
    user_service: UserService = container.resolve(UserService)
    db_user = await user_service.get_user(tg_id=str(message.from_user.id))
    user_language = (
        db_user.language if db_user and db_user.language else DEFAULT_LANGUAGE
    )

    page = 1
    limit = 10
    offset = (page - 1) * limit

    notes = await release_note_service.get_notes(user_language, limit, offset)
    total_count = await release_note_service.count_notes(user_language)
    total_pages = math.ceil(total_count / limit)

    active_message_id = data.get("active_message_id")
    if active_message_id:
        try:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=f"{update_message}\n\n{Dialog.ReleaseNotes.RELEASE_NOTES_MENU}",
                reply_markup=release_notes_menu_ikb(notes, page, total_pages),
            )
            await log_and_set_state(
                message,
                state,
                ReleaseNotesStateManager.menu,
            )
        except Exception as e:
            logger.error("Ошибка при возврате к меню: %s", e, exc_info=True)
            await message.reply(update_message)
    else:
        await message.reply(update_message)


@router.callback_query(
    F.data == CallbackData.ReleaseNotes.CANCEL_EDIT,
    ReleaseNotesStateManager.editing_note,
)
async def cancel_edit_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик отмены редактирования"""
    await callback.answer()

    data = await state.get_data()
    note_id = data.get("edit_note_id")

    if not note_id:
        await callback.answer(Dialog.ReleaseNotes.NOTE_NOT_FOUND, show_alert=True)
        return

    release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)
    note = await release_note_service.get_note_by_id(note_id)

    if not note:
        await callback.answer(Dialog.ReleaseNotes.NOTE_NOT_FOUND, show_alert=True)
        return

    # Получаем автора
    author_name = "Unknown"
    if note.author:
        author_name = note.author.username or str(note.author.tg_id)

    text = Dialog.ReleaseNotes.NOTE_DETAILS.format(
        title=note.title,
        content=note.content,
        author=author_name,
        date=note.created_at.strftime("%d.%m.%Y %H:%M"),
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=release_note_detail_ikb(
            note_id, user_tg_id=str(callback.from_user.id)
        ),
    )

    await log_and_set_state(
        callback.message,
        state,
        ReleaseNotesStateManager.view_note,
    )


@router.callback_query(
    F.data == CallbackData.ReleaseNotes.CANCEL_EDIT,
    ReleaseNotesStateManager.editing_title,
)
@router.callback_query(
    F.data == CallbackData.ReleaseNotes.CANCEL_EDIT,
    ReleaseNotesStateManager.editing_content,
)
async def cancel_edit_title_or_content_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик отмены редактирования заголовка или содержимого"""
    await callback.answer()

    data = await state.get_data()
    note_id = data.get("edit_note_id")

    if not note_id:
        await callback.answer(Dialog.ReleaseNotes.NOTE_NOT_FOUND, show_alert=True)
        return

    release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)
    note = await release_note_service.get_note_by_id(note_id)

    if not note:
        await callback.answer(Dialog.ReleaseNotes.NOTE_NOT_FOUND, show_alert=True)
        return

    # Возвращаемся к окну редактирования заметки
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ReleaseNotes.EDIT_NOTE.format(title=note.title),
        reply_markup=edit_release_note_ikb(),
    )

    await log_and_set_state(
        callback.message,
        state,
        ReleaseNotesStateManager.editing_note,
    )
