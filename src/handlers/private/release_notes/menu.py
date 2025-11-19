import logging
import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from constants.i18n import DEFAULT_LANGUAGE
from container import container
from keyboards.inline.release_notes import release_notes_menu_ikb, select_language_ikb
from services.release_note_service import ReleaseNoteService
from services.user import UserService
from states.release_notes import ReleaseNotesStateManager
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.ReleaseNotes.MENU)
async def release_notes_menu_callback_handler(
    callback: CallbackQuery, state: FSMContext
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
        await log_and_set_state(
            callback.message,
            state,
            ReleaseNotesStateManager.selecting_language,
        )
        return

    # Для обычных пользователей используем их язык
    user_service: UserService = container.resolve(UserService)
    db_user = await user_service.get_user(tg_id=user_tg_id)
    user_language = (
        db_user.language if db_user and db_user.language else DEFAULT_LANGUAGE
    )

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

    await log_and_set_state(
        callback.message,
        state,
        ReleaseNotesStateManager.menu,
    )


@router.callback_query(
    F.data.startswith(CallbackData.ReleaseNotes.PREFIX_PREV_PAGE)
    | F.data.startswith(CallbackData.ReleaseNotes.PREFIX_NEXT_PAGE)
)
async def release_notes_pagination_callback_handler(
    callback: CallbackQuery, state: FSMContext
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
    user_language = data.get("selected_language")

    if not user_language:
        user_service: UserService = container.resolve(UserService)
        db_user = await user_service.get_user(tg_id=str(callback.from_user.id))
        user_language = (
            db_user.language if db_user and db_user.language else DEFAULT_LANGUAGE
        )

    release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)

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
            notes, page, total_pages, user_tg_id=str(callback.from_user.id)
        ),
    )

    await state.update_data(page=page, selected_language=user_language)


@router.callback_query(F.data == CallbackData.ReleaseNotes.BACK)
async def back_to_release_notes_menu_callback_handler(
    callback: CallbackQuery, state: FSMContext
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
        await log_and_set_state(
            callback.message,
            state,
            ReleaseNotesStateManager.selecting_language,
        )
        return

    # Для обычных пользователей используем их язык
    await release_notes_menu_callback_handler(callback, state)


@router.callback_query(F.data == CallbackData.ReleaseNotes.PAGE_INFO)
async def page_info_callback_handler(callback: CallbackQuery) -> None:
    """Обработчик нажатия на кнопку с информацией о странице (пустышка)"""
    await callback.answer()


@router.callback_query(
    F.data.startswith(CallbackData.ReleaseNotes.PREFIX_SELECT_LANGUAGE),
    ReleaseNotesStateManager.selecting_language,
)
async def select_language_handler(callback: CallbackQuery, state: FSMContext) -> None:
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
    await log_and_set_state(
        callback.message,
        state,
        ReleaseNotesStateManager.menu,
    )
