import logging
from typing import List

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants.callback import CallbackData
from constants.pagination import CHATS_PAGE_SIZE
from dto.chat_dto import ChatDTO
from keyboards.inline.chats import (
    chat_actions_ikb,
    chats_management_ikb,
    show_tracked_chats_ikb,
)
from states import ChatStateManager
from usecases.chat import GetTrackedChatsUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Chat.SELECT_CHAT_FOR_REPORT)
@router.callback_query(F.data == CallbackData.Chat.SELECT_CHAT_FOR_SETTINGS)
async def show_tracked_chats_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик возврата к выбору чата из действий с чатом."""
    await callback.answer()

    tg_id = str(callback.from_user.id)

    try:
        usecase: GetTrackedChatsUseCase = container.resolve(GetTrackedChatsUseCase)
        chats = await usecase.execute(tg_id=tg_id)
    except Exception as e:
        await _handle_error(callback=callback, error=e)
        return

    if not chats:
        await _show_no_chats_message(callback=callback)
        return

    # Устанавливаем состояние выбора чата
    if callback.data == CallbackData.Chat.SELECT_CHAT_FOR_REPORT:
        await state.set_state(ChatStateManager.selecting_chat_for_report)
        await _show_chats_list_message(
            callback=callback,
            chats=chats,
            back_callback=CallbackData.Analytics.SHOW_MENU,
            show_management_button=True,
            prev_page_prefix=CallbackData.Chat.PREFIX_PREV_CHATS_REPORT_PAGE,
            next_page_prefix=CallbackData.Chat.PREFIX_NEXT_CHATS_REPORT_PAGE,
        )
    else:
        await state.set_state(ChatStateManager.listing_tracking_chats)
        await _show_chats_list_message(
            callback=callback,
            chats=chats,
            back_callback=CallbackData.Chat.SHOW_MENU,
            show_management_button=False,
            prev_page_prefix=CallbackData.Chat.PREFIX_PREV_CHATS_PAGE,
            next_page_prefix=CallbackData.Chat.PREFIX_NEXT_CHATS_PAGE,
        )


async def _show_no_chats_message(callback: CallbackQuery) -> None:
    """Показывает сообщение о том, что нет отслеживаемых чатов."""
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="❗Чтобы получать отчёты по чату, необходимо добавить чат "
        "в отслеживаемые, а также пользователей для сбора статистики",
        reply_markup=chats_management_ikb(),
    )


async def _show_chats_list_message(
    callback: CallbackQuery,
    chats: List[ChatDTO],
    *,
    back_callback: str,
    show_management_button: bool,
    prev_page_prefix: str,
    next_page_prefix: str,
) -> None:
    """Показывает список чатов на первой странице."""
    # Получаем первую страницу чатов
    first_page_chats = chats[:CHATS_PAGE_SIZE]

    message_text = f"Найдено {len(chats)} чат(-ов):"
    total_count = len(chats)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=message_text,
        reply_markup=show_tracked_chats_ikb(
            chats=first_page_chats,
            page=1,
            total_count=total_count,
            back_callback=back_callback,
            show_management_button=show_management_button,
            prev_page_prefix=prev_page_prefix,
            next_page_prefix=next_page_prefix,
        ),
    )


async def _handle_error(callback: CallbackQuery, error: Exception) -> None:
    """Обрабатывает ошибки при получении списка чатов."""
    logger.error(f"Ошибка при получении списка чатов: {error}")
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="❌ Ошибка при получении списка чатов",
        reply_markup=chat_actions_ikb(),
    )
