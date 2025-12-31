import logging
import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from constants.i18n import DEFAULT_LANGUAGE
from container import container
from keyboards.inline.release_notes import (
    confirm_delete_release_note_ikb,
    release_notes_menu_ikb,
)
from services.release_note_service import ReleaseNoteService
from services.user import UserService
from states.release_notes import ReleaseNotesStateManager
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith(f"{CallbackData.ReleaseNotes.DELETE}__"))
async def delete_note_start_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала удаления релизной заметки"""
    from constants import RELEASE_NOTES_ADMIN_IDS

    await callback.answer()

    # Проверка прав доступа
    user_tg_id = str(callback.from_user.id)
    if user_tg_id not in RELEASE_NOTES_ADMIN_IDS:
        await callback.answer("У вас нет прав для удаления заметок", show_alert=True)
        return

    note_id = int(callback.data.split("__")[1])

    release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)
    note = await release_note_service.get_note_by_id(note_id)

    if not note:
        await callback.answer(Dialog.ReleaseNotes.NOTE_NOT_FOUND, show_alert=True)
        return

    await state.update_data(delete_note_id=note_id)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ReleaseNotes.DELETE_CONFIRM,
        reply_markup=confirm_delete_release_note_ikb(note_id),
    )

    await state.set_state(ReleaseNotesStateManager.deleting_note)


@router.callback_query(
    F.data.startswith(CallbackData.ReleaseNotes.PREFIX_CONFIRM_DELETE),
    ReleaseNotesStateManager.deleting_note,
)
async def confirm_delete_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик подтверждения удаления"""
    from constants import RELEASE_NOTES_ADMIN_IDS

    await callback.answer()

    # Проверка прав доступа
    user_tg_id = str(callback.from_user.id)
    if user_tg_id not in RELEASE_NOTES_ADMIN_IDS:
        await callback.answer("У вас нет прав для удаления заметок", show_alert=True)
        return

    parts = callback.data.split("__")
    answer = parts[1]
    note_id = int(parts[2])

    if answer != "yes":
        # Возвращаемся к просмотру заметки
        release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)
        note = await release_note_service.get_note_by_id(note_id)

        if not note:
            await callback.answer(Dialog.ReleaseNotes.NOTE_NOT_FOUND, show_alert=True)
            return

        from keyboards.inline.release_notes import release_note_detail_ikb

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
            text=f"{Dialog.ReleaseNotes.DELETE_CANCELLED}\n\n{text}",
            reply_markup=release_note_detail_ikb(
                note_id, user_tg_id=str(callback.from_user.id)
            ),
        )

        await state.set_state(ReleaseNotesStateManager.view_note)
        return

    try:
        release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)
        success = await release_note_service.delete_note(note_id)

        if not success:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=Dialog.ReleaseNotes.DELETE_ERROR,
            )
            return

        # Возвращаемся к меню релизных заметок
        user_service: UserService = container.resolve(UserService)
        db_user = await user_service.get_user(tg_id=str(callback.from_user.id))
        user_language = (
            db_user.language if db_user and db_user.language else DEFAULT_LANGUAGE
        )

        page = 1
        limit = 10
        offset = (page - 1) * limit

        notes = await release_note_service.get_notes(user_language, limit, offset)
        total_count = await release_note_service.count_notes(user_language)
        total_pages = math.ceil(total_count / limit)

        if not notes:
            text = Dialog.ReleaseNotes.NO_RELEASE_NOTES
        else:
            text = Dialog.ReleaseNotes.RELEASE_NOTES_MENU

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"{Dialog.ReleaseNotes.DELETE_SUCCESS}\n\n{text}",
            reply_markup=release_notes_menu_ikb(
                notes, page, total_pages, user_tg_id=str(callback.from_user.id)
            ),
        )

        await state.set_state(ReleaseNotesStateManager.menu)

    except Exception as e:
        logger.error("Ошибка при удалении заметки: %s", e, exc_info=True)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.ReleaseNotes.DELETE_ERROR,
        )
