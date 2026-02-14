"""Пагинация списка релизных заметок."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from constants.pagination import RELEASE_NOTES_PAGE_SIZE
from dto.release_note import GetReleaseNotesPageDTO
from keyboards.inline.release_notes import release_notes_menu_ikb
from usecases.release_notes import GetReleaseNotesPageUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data.startswith(CallbackData.ReleaseNotes.PREFIX_PREV_PAGE)
    | F.data.startswith(CallbackData.ReleaseNotes.PREFIX_NEXT_PAGE)
)
async def release_notes_pagination_callback_handler(
    callback: CallbackQuery, state: FSMContext, container: Container, user_language: str
) -> None:
    """Обработчик пагинации релизных заметок."""
    await callback.answer()
    if callback.data is None or callback.message is None:
        return
    if not isinstance(callback.message, Message):
        return

    if callback.data.startswith(CallbackData.ReleaseNotes.PREFIX_PREV_PAGE):
        page = int(callback.data.split(CallbackData.ReleaseNotes.PREFIX_PREV_PAGE)[1])
    else:
        page = int(callback.data.split(CallbackData.ReleaseNotes.PREFIX_NEXT_PAGE)[1])

    data = await state.get_data()
    selected_language = data.get("selected_language") or user_language

    dto = GetReleaseNotesPageDTO(
        language=selected_language, page=page, page_size=RELEASE_NOTES_PAGE_SIZE
    )
    usecase: GetReleaseNotesPageUseCase = container.resolve(GetReleaseNotesPageUseCase)
    result = await usecase.execute(dto)

    text = (
        Dialog.ReleaseNotes.NO_RELEASE_NOTES
        if not result.notes
        else Dialog.ReleaseNotes.RELEASE_NOTES_MENU
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=release_notes_menu_ikb(
            result.notes, result.page, result.total_pages
        ),
    )

    await state.update_data(page=page, selected_language=selected_language)


@router.callback_query(F.data == CallbackData.ReleaseNotes.PAGE_INFO)
async def page_info_callback_handler(callback: CallbackQuery) -> None:
    """Обработчик нажатия на кнопку с информацией о странице (пустышка)."""
    await callback.answer()
