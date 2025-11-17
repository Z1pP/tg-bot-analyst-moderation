from typing import List, Tuple

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from constants.pagination import CHATS_PAGE_SIZE
from container import container
from keyboards.inline.chats_kb import remove_chat_ikb, tracked_chats_ikb
from models import ChatSession
from usecases.chat import GetTrackedChatsUseCase
from utils.pagination_handler import BasePaginationHandler

router = Router(name=__name__)


class ChatsPaginationHandler(BasePaginationHandler):
    def __init__(self):
        super().__init__("чатов")

    async def get_page_data(
        self,
        page: int,
        callback: CallbackQuery,
        state: FSMContext,
    ) -> Tuple[List[ChatSession], int]:
        chats = await get_tracked_chats(callback.from_user.username)
        chats_page, total_count = paginate_chats(chats, page)
        return chats_page, total_count

    async def build_keyboard(
        self,
        items: List[ChatSession],
        page: int,
        total_count: int,
    ) -> InlineKeyboardMarkup:
        return tracked_chats_ikb(
            chats=items,
            page=page,
            total_count=total_count,
        )


class RemoveChatsPaginationHandler(BasePaginationHandler):
    def __init__(self):
        super().__init__("чатов")

    async def get_page_data(
        self,
        page: int,
        callback: CallbackQuery,
        state: FSMContext,
    ) -> Tuple[List[ChatSession], int]:
        chats = await get_tracked_chats(callback.from_user.username)
        chats_page, total_count = paginate_chats(chats, page)
        return chats_page, total_count

    async def build_keyboard(
        self,
        items: List[ChatSession],
        page: int,
        total_count: int,
    ) -> InlineKeyboardMarkup:
        return remove_chat_ikb(
            chats=items,
            page=page,
            total_count=total_count,
        )


chats_handler = ChatsPaginationHandler()
remove_chats_handler = RemoveChatsPaginationHandler()


@router.callback_query(F.data.startswith("prev_chats_page__"))
async def prev_chats_page_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await chats_handler.handle_prev_page(callback, state)


@router.callback_query(F.data.startswith("next_chats_page__"))
async def next_chats_page_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await chats_handler.handle_next_page(callback, state)


@router.callback_query(F.data.startswith("prev_remove_chats_page__"))
async def prev_remove_chats_page_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await remove_chats_handler.handle_prev_page(callback, state)


@router.callback_query(F.data.startswith("next_remove_chats_page__"))
async def next_remove_chats_page_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await remove_chats_handler.handle_next_page(callback, state)


async def get_tracked_chats(admin_username: str) -> List[ChatSession]:
    """Получает все отслеживаемые чаты."""
    usecase: GetTrackedChatsUseCase = container.resolve(GetTrackedChatsUseCase)
    return await usecase.execute(username=admin_username)


def paginate_chats(
    chats: List[ChatSession],
    page: int,
    page_size: int = CHATS_PAGE_SIZE,
) -> tuple[List[ChatSession], int]:
    """Разбивает список чатов на страницы."""

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    return chats[start_idx:end_idx], len(chats)
