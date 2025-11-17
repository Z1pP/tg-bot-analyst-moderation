import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from constants.pagination import CHATS_PAGE_SIZE
from container import container
from keyboards.inline.chats_kb import chat_actions_ikb, tracked_chats_ikb
from states import ChatStateManager, TemplateStateManager
from usecases.chat import GetTrackedChatsUseCase
from utils.exception_handler import handle_exception
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("chat__"))
async def chat_selected_handler(
    query: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик выбора чата из списка чатов.
    """
    try:
        chat_id = int(query.data.split("__")[1])

        await log_and_set_state(
            message=query.message,
            state=state,
            new_state=ChatStateManager.selecting_chat,
        )
        await state.update_data(chat_id=chat_id)

        await query.message.edit_text(
            text=Dialog.Chat.SELECT_ACTION,
            reply_markup=chat_actions_ikb(),
        )

        await query.answer()

    except Exception as e:
        await handle_exception(
            message=query.message, exc=e, context="chat_selected_handler"
        )


@router.callback_query(
    TemplateStateManager.process_template_chat,
    F.data.startswith("template_scope__"),
)
async def process_template_chat_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик выбора чата из списка чатов.
    """
    await callback.answer()

    chat_id = int(callback.data.split("__")[1])

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

    await callback.answer()


@router.callback_query(F.data == CallbackData.Chat.GET_STATISTICS)
@router.callback_query(F.data == CallbackData.Chat.SELECT_ANOTHER_CHAT)
async def get_list_tracked_chats_handler(
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
