import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from constants.pagination import CHATS_PAGE_SIZE
from container import container
from keyboards.inline.chats import (
    chat_actions_ikb,
    chats_management_ikb,
    tracked_chats_ikb,
)
from services.chat import ChatService
from states import ChatStateManager, TemplateStateManager
from usecases.chat import GetTrackedChatsUseCase
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith(CallbackData.Chat.PREFIX_CHAT))
async def chat_selected_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик выбора чата из списка чатов.
    """
    await callback.answer()

    chat_id = int(callback.data.replace(CallbackData.Chat.PREFIX_CHAT, ""))

    chat_service: ChatService = container.resolve(ChatService)
    chat = await chat_service.get_chat_with_archive(chat_id=chat_id)

    if not chat:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
            reply_markup=chats_management_ikb(),
        )
        return

    await state.update_data(chat_id=chat_id)

    await callback.message.edit_text(
        text=Dialog.Chat.CHAT_ACTIONS.format(title=chat.title),
        reply_markup=chat_actions_ikb(),
    )


@router.callback_query(F.data == CallbackData.Chat.BACK_TO_CHAT_ACTIONS)
async def back_to_chat_actions_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик возврата к меню чатов."""
    await callback.answer()

    chat_id = await state.get_value("chat_id")

    chat_service: ChatService = container.resolve(ChatService)
    chat = await chat_service.get_chat_with_archive(chat_id=chat_id)

    if not chat:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
            reply_markup=chats_management_ikb(),
        )
        return

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.CHAT_ACTIONS.format(title=chat.title),
        reply_markup=chat_actions_ikb(),
    )


@router.callback_query(
    TemplateStateManager.process_template_chat,
    F.data.startswith(CallbackData.Chat.PREFIX_TEMPLATE_SCOPE),
)
async def process_template_chat_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик выбора чата из списка чатов.
    """
    await callback.answer()

    chat_id = int(callback.data.replace(CallbackData.Chat.PREFIX_TEMPLATE_SCOPE, ""))

    if chat_id == -1:
        await state.update_data(chat_id=None)
    else:
        await state.update_data(chat_id=int(chat_id))

    text = Dialog.Chat.ENTER_TEMPLATE_NAME

    await callback.message.answer(text=text)

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=TemplateStateManager.process_template_title,
    )


@router.callback_query(F.data == CallbackData.Chat.SELECT_CHAT)
async def show_tracked_chats_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик возврата к выбору чата из действий с чатом."""
    await callback.answer()

    tg_id = str(callback.from_user.id)
    try:
        usecase: GetTrackedChatsUseCase = container.resolve(GetTrackedChatsUseCase)
        chats = await usecase.execute(tg_id=tg_id)
    except Exception as e:
        logger.error(f"Ошибка при получении списка чатов: {e}")
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ Ошибка при получении списка чатов",
            reply_markup=chat_actions_ikb(),
        )
        return

    if not chats:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❗Чтобы получать отчёты по чату, необходимо добавить чат "
            "в отслеживаемые, а также пользователей для сбора статистики",
            reply_markup=chat_actions_ikb(),
        )
        return

    # Показываем первую страницу
    first_page_chats = chats[:CHATS_PAGE_SIZE]

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"Найдено {len(chats)} чат(-ов):",
        reply_markup=tracked_chats_ikb(
            chats=first_page_chats, page=1, total_count=len(chats)
        ),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=ChatStateManager.listing_tracking_chats,
    )
