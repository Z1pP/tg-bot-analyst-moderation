import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.release_notes import release_note_detail_ikb
from services.release_note_service import ReleaseNoteService
from services.time_service import TimeZoneService
from states.release_notes import ReleaseNotesStateManager
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith(CallbackData.ReleaseNotes.PREFIX_SELECT))
async def view_note_callback_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик просмотра детализации релизной заметки"""
    await callback.answer()

    note_id = int(callback.data.split(CallbackData.ReleaseNotes.PREFIX_SELECT)[1])

    release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)
    note = await release_note_service.get_note_by_id(note_id)

    if not note:
        await callback.answer("Заметка не найдена", show_alert=True)
        return

    # Получаем автора
    author_name = "Unknown"
    if note.author:
        author_name = note.author.username or str(note.author.tg_id)

    note.created_at = TimeZoneService.convert_to_local_time(note.created_at)

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

    await state.set_state(ReleaseNotesStateManager.view_note)
