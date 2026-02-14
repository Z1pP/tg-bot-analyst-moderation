"""Пагинация списка релизных заметок."""

import logging
from typing import Sequence

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.release_notes import release_notes_menu_ikb
from models.release_note import ReleaseNote
from services.release_note_service import ReleaseNoteService
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)

RELEASE_NOTES_PAGE_SIZE = 10


def calc_offset(page: int, page_size: int) -> int:
    """Вычисляет смещение для страницы."""
    return (page - 1) * page_size


def calc_total_pages(total_count: int, page_size: int) -> int:
    """Вычисляет общее количество страниц."""
    if page_size <= 0:
        return 0
    return (total_count + page_size - 1) // page_size


async def get_notes_page_data(
    service: ReleaseNoteService, language: str, page: int
) -> tuple[Sequence[ReleaseNote], int]:
    """
    Возвращает данные одной страницы заметок: (notes, total_pages).
    """
    limit = RELEASE_NOTES_PAGE_SIZE
    offset = calc_offset(page, limit)
    notes = await service.get_notes(language, limit, offset)
    total_count = await service.count_notes(language)
    total_pages = calc_total_pages(total_count, limit)
    return notes, total_pages


@router.callback_query(
    F.data.startswith(CallbackData.ReleaseNotes.PREFIX_PREV_PAGE)
    | F.data.startswith(CallbackData.ReleaseNotes.PREFIX_NEXT_PAGE)
)
async def release_notes_pagination_callback_handler(
    callback: CallbackQuery, state: FSMContext, container: Container, user_language: str
) -> None:
    """Обработчик пагинации релизных заметок."""
    await callback.answer()

    if callback.data.startswith(CallbackData.ReleaseNotes.PREFIX_PREV_PAGE):
        page = int(callback.data.split(CallbackData.ReleaseNotes.PREFIX_PREV_PAGE)[1])
    else:
        page = int(callback.data.split(CallbackData.ReleaseNotes.PREFIX_NEXT_PAGE)[1])

    data = await state.get_data()
    selected_language = data.get("selected_language") or user_language

    release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)
    notes, total_pages = await get_notes_page_data(
        release_note_service, selected_language, page
    )

    if not notes:
        text = Dialog.ReleaseNotes.NO_RELEASE_NOTES
    else:
        text = Dialog.ReleaseNotes.RELEASE_NOTES_MENU

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=release_notes_menu_ikb(notes, page, total_pages),
    )

    await state.update_data(page=page, selected_language=selected_language)


@router.callback_query(F.data == CallbackData.ReleaseNotes.PAGE_INFO)
async def page_info_callback_handler(callback: CallbackQuery) -> None:
    """Обработчик нажатия на кнопку с информацией о странице (пустышка)."""
    await callback.answer()
