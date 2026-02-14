import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from dto.release_note import GetReleaseNoteByIdDTO
from exceptions import ReleaseNoteNotFoundError
from keyboards.inline.release_notes import release_note_detail_ikb
from states.release_notes import ReleaseNotesStateManager
from usecases.release_notes import GetReleaseNoteUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith(CallbackData.ReleaseNotes.PREFIX_SELECT))
async def view_note_callback_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик просмотра детализации релизной заметки."""
    await callback.answer()
    if callback.data is None or callback.message is None:
        return
    if not isinstance(callback.message, Message):
        return

    note_id = int(callback.data.split(CallbackData.ReleaseNotes.PREFIX_SELECT)[1])

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
        text=text,
        reply_markup=release_note_detail_ikb(result.note_id),
    )

    await state.set_state(ReleaseNotesStateManager.view_note)
