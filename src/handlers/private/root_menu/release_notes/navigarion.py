import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from constants.pagination import RELEASE_NOTES_PAGE_SIZE
from dto.release_note import GetReleaseNotesPageDTO
from keyboards.inline.release_notes import release_notes_menu_ikb, select_language_ikb
from states.release_notes import ReleaseNotesStateManager
from usecases.release_notes import GetReleaseNotesPageUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.ReleaseNotes.SHOW_MENU)
async def release_notes_menu_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Отображает главное меню релизных заметок (выбор языка)."""
    await callback.answer()
    if callback.message is None or not isinstance(callback.message, Message):
        return
    await state.clear()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ReleaseNotes.SELECT_LANGUAGE,
        reply_markup=select_language_ikb(),
    )
    await state.set_state(ReleaseNotesStateManager.selecting_language)


@router.callback_query(F.data == CallbackData.ReleaseNotes.BACK)
async def back_to_release_notes_menu_callback_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик возврата в меню релизных заметок."""
    await callback.answer()
    if callback.message is None or not isinstance(callback.message, Message):
        return
    await state.clear()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ReleaseNotes.SELECT_LANGUAGE,
        reply_markup=select_language_ikb(),
    )
    await state.set_state(ReleaseNotesStateManager.selecting_language)


@router.callback_query(
    F.data.startswith(CallbackData.ReleaseNotes.PREFIX_SELECT_LANGUAGE),
    ReleaseNotesStateManager.selecting_language,
)
async def select_language_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик выбора языка для просмотра заметок"""
    await callback.answer()
    if callback.data is None or callback.message is None:
        return
    if not isinstance(callback.message, Message):
        return

    lang_code = callback.data.split(CallbackData.ReleaseNotes.PREFIX_SELECT_LANGUAGE)[1]

    dto = GetReleaseNotesPageDTO(
        language=lang_code, page=1, page_size=RELEASE_NOTES_PAGE_SIZE
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

    await state.update_data(selected_language=lang_code, page=result.page)
    await state.set_state(ReleaseNotesStateManager.menu)
