import logging
import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.release_notes import release_notes_menu_ikb, select_language_ikb
from services.release_note_service import ReleaseNoteService
from states.release_notes import ReleaseNotesStateManager
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.ReleaseNotes.SHOW_MENU)
async def release_notes_menu_callback_handler(
    callback: CallbackQuery, state: FSMContext, container: Container, user_language: str
) -> None:
    """Обработчик меню релизных заметок"""
    from constants import RELEASE_NOTES_ADMIN_IDS

    await callback.answer()
    await state.clear()

    user_tg_id = str(callback.from_user.id)

    # Для админов показываем выбор языка
    if user_tg_id in RELEASE_NOTES_ADMIN_IDS:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.ReleaseNotes.SELECT_LANGUAGE,
            reply_markup=select_language_ikb(),
        )
        await state.set_state(ReleaseNotesStateManager.selecting_language)
        return

    release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)

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
        text=text,
        reply_markup=release_notes_menu_ikb(
            notes, page, total_pages, user_tg_id=user_tg_id
        ),
    )

    await state.set_state(ReleaseNotesStateManager.menu)


@router.callback_query(
    F.data.startswith(CallbackData.ReleaseNotes.PREFIX_PREV_PAGE)
    | F.data.startswith(CallbackData.ReleaseNotes.PREFIX_NEXT_PAGE)
)
async def release_notes_pagination_callback_handler(
    callback: CallbackQuery, state: FSMContext, container: Container, user_language: str
) -> None:
    """Обработчик пагинации релизных заметок"""
    await callback.answer()

    # Получаем номер страницы из callback_data
    if callback.data.startswith(CallbackData.ReleaseNotes.PREFIX_PREV_PAGE):
        page = int(callback.data.split(CallbackData.ReleaseNotes.PREFIX_PREV_PAGE)[1])
    else:
        page = int(callback.data.split(CallbackData.ReleaseNotes.PREFIX_NEXT_PAGE)[1])

    # Получаем язык из state или используем язык пользователя
    data = await state.get_data()
    selected_language = data.get("selected_language") or user_language

    release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)

    limit = 10
    offset = (page - 1) * limit

    notes = await release_note_service.get_notes(selected_language, limit, offset)
    total_count = await release_note_service.count_notes(selected_language)
    total_pages = math.ceil(total_count / limit)

    if not notes:
        text = Dialog.ReleaseNotes.NO_RELEASE_NOTES
    else:
        text = Dialog.ReleaseNotes.RELEASE_NOTES_MENU

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=release_notes_menu_ikb(
            notes, page, total_pages, user_tg_id=str(callback.from_user.id)
        ),
    )

    await state.update_data(page=page, selected_language=selected_language)


@router.callback_query(F.data == CallbackData.ReleaseNotes.BACK)
async def back_to_release_notes_menu_callback_handler(
    callback: CallbackQuery, state: FSMContext, container: Container, user_language: str
) -> None:
    """Обработчик возврата в меню релизных заметок"""
    from constants import RELEASE_NOTES_ADMIN_IDS

    await callback.answer()
    await state.clear()

    user_tg_id = str(callback.from_user.id)

    # Для админов показываем выбор языка
    if user_tg_id in RELEASE_NOTES_ADMIN_IDS:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.ReleaseNotes.SELECT_LANGUAGE,
            reply_markup=select_language_ikb(),
        )
        await state.set_state(ReleaseNotesStateManager.selecting_language)
        return

    # Для обычных пользователей используем их язык
    await release_notes_menu_callback_handler(callback, state, container, user_language)


@router.callback_query(F.data == CallbackData.ReleaseNotes.PAGE_INFO)
async def page_info_callback_handler(callback: CallbackQuery) -> None:
    """Обработчик нажатия на кнопку с информацией о странице (пустышка)"""
    await callback.answer()


@router.callback_query(
    F.data.startswith(CallbackData.ReleaseNotes.PREFIX_SELECT_LANGUAGE),
    ReleaseNotesStateManager.selecting_language,
)
async def select_language_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик выбора языка для просмотра заметок"""
    await callback.answer()

    # Извлекаем язык из callback_data
    lang_code = callback.data.split(CallbackData.ReleaseNotes.PREFIX_SELECT_LANGUAGE)[1]

    release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)

    page = 1
    limit = 10
    offset = (page - 1) * limit

    notes = await release_note_service.get_notes(lang_code, limit, offset)
    total_count = await release_note_service.count_notes(lang_code)
    total_pages = math.ceil(total_count / limit)

    if not notes:
        text = Dialog.ReleaseNotes.NO_RELEASE_NOTES
    else:
        text = Dialog.ReleaseNotes.RELEASE_NOTES_MENU

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=release_notes_menu_ikb(
            notes, page, total_pages, user_tg_id=str(callback.from_user.id)
        ),
    )

    await state.update_data(selected_language=lang_code, page=page)
    await state.set_state(ReleaseNotesStateManager.menu)
