import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants.callback import CallbackData
from constants.pagination import CHATS_PAGE_SIZE
from container import container
from keyboards.inline.chats import (
    chat_actions_ikb,
    chats_management_ikb,
    tracked_chats_ikb,
)
from states import ChatStateManager
from usecases.chat import GetTrackedChatsUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


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
            reply_markup=chats_management_ikb(),
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

    await state.set_state(ChatStateManager.listing_tracking_chats)
