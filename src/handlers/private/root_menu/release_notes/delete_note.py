import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from constants.pagination import RELEASE_NOTES_PAGE_SIZE
from dto.release_note import (
    DeleteReleaseNoteDTO,
    GetReleaseNoteByIdDTO,
    GetReleaseNotesPageDTO,
)
from exceptions import ReleaseNoteNotFoundError
from keyboards.inline.release_notes import (
    confirm_delete_release_note_ikb,
    release_note_detail_ikb,
    release_notes_menu_ikb,
)
from states.release_notes import ReleaseNotesStateManager
from usecases.release_notes import (
    DeleteReleaseNoteUseCase,
    GetReleaseNotesPageUseCase,
    GetReleaseNoteUseCase,
)
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith(f"{CallbackData.ReleaseNotes.DELETE}__"))
async def delete_note_start_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик начала удаления релизной заметки"""
    await callback.answer()
    if callback.data is None or callback.message is None:
        return
    if not isinstance(callback.message, Message):
        return

    note_id = int(callback.data.split("__")[1])

    dto = GetReleaseNoteByIdDTO(note_id=note_id)
    usecase: GetReleaseNoteUseCase = container.resolve(GetReleaseNoteUseCase)
    try:
        await usecase.execute(dto)
    except ReleaseNoteNotFoundError as e:
        await callback.answer(e.get_user_message(), show_alert=True)
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
async def confirm_delete_handler(
    callback: CallbackQuery, state: FSMContext, container: Container, user_language: str
) -> None:
    """Обработчик подтверждения удаления"""
    await callback.answer()
    if callback.data is None or callback.message is None:
        return
    if not isinstance(callback.message, Message):
        return

    parts = callback.data.split("__")
    answer = parts[1]
    note_id = int(parts[2])

    if answer != "yes":
        dto = GetReleaseNoteByIdDTO(note_id=note_id)
        usecase: GetReleaseNoteUseCase = container.resolve(GetReleaseNoteUseCase)
        try:
            result = await usecase.execute(dto)
        except ReleaseNoteNotFoundError as e:
            await callback.answer(e.get_user_message(), show_alert=True)
            return

        text = Dialog.ReleaseNotes.NOTE_DETAILS.format(
            title=result.title,
            content=result.content,
            author=result.author_display_name,
            date=result.date_str,
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"{Dialog.ReleaseNotes.DELETE_CANCELLED}\n\n{text}",
            reply_markup=release_note_detail_ikb(result.note_id),
        )

        await state.set_state(ReleaseNotesStateManager.view_note)
        return

    try:
        delete_dto = DeleteReleaseNoteDTO(note_id=note_id)
        delete_usecase: DeleteReleaseNoteUseCase = container.resolve(
            DeleteReleaseNoteUseCase
        )
        await delete_usecase.execute(delete_dto)
    except ReleaseNoteNotFoundError:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.ReleaseNotes.DELETE_ERROR,
        )
        return
    except Exception as e:
        logger.error("Ошибка при удалении заметки: %s", e, exc_info=True)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.ReleaseNotes.DELETE_ERROR,
        )
        return

    page_dto = GetReleaseNotesPageDTO(
        language=user_language, page=1, page_size=RELEASE_NOTES_PAGE_SIZE
    )
    page_usecase: GetReleaseNotesPageUseCase = container.resolve(
        GetReleaseNotesPageUseCase
    )
    page_result = await page_usecase.execute(page_dto)

    text = (
        Dialog.ReleaseNotes.NO_RELEASE_NOTES
        if not page_result.notes
        else Dialog.ReleaseNotes.RELEASE_NOTES_MENU
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"{Dialog.ReleaseNotes.DELETE_SUCCESS}\n\n{text}",
        reply_markup=release_notes_menu_ikb(
            page_result.notes, page_result.page, page_result.total_pages
        ),
    )

    await state.set_state(ReleaseNotesStateManager.menu)
