"""Обработчики пагинации выбора чата для отправки сообщения."""

from typing import List, Optional, Tuple

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from constants.pagination import CHATS_PAGE_SIZE
from dto import ChatDTO
from keyboards.inline.chats import select_chat_ikb
from keyboards.inline.message_actions import send_message_ikb
from states.message_management import MessageManagerState
from usecases.chat_tracking import GetUserTrackedChatsUseCase
from utils.pagination_handler import BasePaginationHandler
from utils.send_message import safe_edit_message

router = Router(name=__name__)


class SelectChatPaginationHandler(BasePaginationHandler):
    """Обработчик пагинации при выборе чата для отправки сообщения."""

    def __init__(self):
        super().__init__("чатов")

    async def get_page_data(
        self,
        page: int,
        callback: CallbackQuery,
        state: FSMContext,
        container: Optional[Container] = None,
    ) -> Tuple[List[ChatDTO], int]:
        usecase: GetUserTrackedChatsUseCase = container.resolve(
            GetUserTrackedChatsUseCase
        )
        user_chats_dto = await usecase.execute(tg_id=str(callback.from_user.id))
        chats = user_chats_dto.chats
        total_count = len(chats)

        start_idx = (page - 1) * CHATS_PAGE_SIZE
        end_idx = start_idx + CHATS_PAGE_SIZE
        chats_page = chats[start_idx:end_idx]

        return chats_page, total_count

    async def build_keyboard(
        self,
        items: List[ChatDTO],
        page: int,
        total_count: int,
    ) -> InlineKeyboardMarkup:
        return select_chat_ikb(
            chats=items,
            page=page,
            total_count=total_count,
        )

    async def handle_prev_page(
        self,
        query: CallbackQuery,
        state: FSMContext,
        container: Optional[Container] = None,
    ) -> None:
        """Обработчик перехода на предыдущую страницу."""
        await query.answer()

        current_page = int(query.data.split("__")[1])
        prev_page = max(1, current_page - 1)

        items, total_count = await self.get_page_data(
            prev_page, query, state, container
        )

        if total_count == 0:
            await safe_edit_message(
                bot=query.bot,
                chat_id=query.message.chat.id,
                message_id=query.message.message_id,
                text=Dialog.Messages.NO_TRACKED_CHATS,
                reply_markup=send_message_ikb(),
            )
            await state.clear()
            return

        keyboard = await self.build_keyboard(items, prev_page, total_count)
        await safe_edit_message(
            bot=query.bot,
            chat_id=query.message.chat.id,
            message_id=query.message.message_id,
            text=Dialog.Messages.SELECT_CHAT,
            reply_markup=keyboard,
        )

    async def handle_next_page(
        self,
        query: CallbackQuery,
        state: FSMContext,
        container: Optional[Container] = None,
    ) -> None:
        """Обработчик перехода на следующую страницу."""
        current_page = int(query.data.split("__")[1])
        next_page = current_page + 1

        items, total_count = await self.get_page_data(
            next_page, query, state, container
        )

        if total_count == 0:
            await query.answer()
            await safe_edit_message(
                bot=query.bot,
                chat_id=query.message.chat.id,
                message_id=query.message.message_id,
                text=Dialog.Messages.NO_TRACKED_CHATS,
                reply_markup=send_message_ikb(),
            )
            await state.clear()
            return

        if not items:
            await query.answer(f"Больше {self.entity_name} нет")
            return

        await query.answer()
        keyboard = await self.build_keyboard(items, next_page, total_count)
        await safe_edit_message(
            bot=query.bot,
            chat_id=query.message.chat.id,
            message_id=query.message.message_id,
            text=Dialog.Messages.SELECT_CHAT,
            reply_markup=keyboard,
        )


select_chat_pagination_handler = SelectChatPaginationHandler()


@router.callback_query(
    MessageManagerState.waiting_select_chat,
    F.data == CallbackData.Messages.SELECT_CHAT_PAGE_INFO,
)
async def select_chat_page_info_handler(callback: types.CallbackQuery) -> None:
    """Обработчик нажатия на кнопку информации о странице (закрывает loading)."""
    await callback.answer()


@router.callback_query(
    MessageManagerState.waiting_select_chat,
    F.data.startswith(CallbackData.Messages.PREFIX_PREV_SELECT_CHAT_PAGE),
)
async def prev_select_chat_page_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик перехода на предыдущую страницу выбора чата."""
    await select_chat_pagination_handler.handle_prev_page(callback, state, container)


@router.callback_query(
    MessageManagerState.waiting_select_chat,
    F.data.startswith(CallbackData.Messages.PREFIX_NEXT_SELECT_CHAT_PAGE),
)
async def next_select_chat_page_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик перехода на следующую страницу выбора чата."""
    await select_chat_pagination_handler.handle_next_page(callback, state, container)
