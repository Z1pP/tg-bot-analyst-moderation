from typing import List, Tuple

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from punq import Container

from constants.callback import CallbackData
from dto.user import UserDTO
from keyboards.inline.users import remove_user_inline_kb
from states import UserStateManager
from utils.pagination_handler import BasePaginationHandler

from .list import get_tracked_users, paginate_users

router = Router(name=__name__)


class RemoveUsersPaginationHandler(BasePaginationHandler):
    """Обработчик пагинации для удаления пользователей."""

    def __init__(self):
        super().__init__("пользователей")

    async def get_page_data(
        self,
        page: int,
        query: CallbackQuery,
        state: FSMContext,
        container: Container,
    ) -> Tuple[List[UserDTO], int]:
        users = await get_tracked_users(str(query.from_user.id), container)
        return paginate_users(users, page)

    async def build_keyboard(
        self,
        items: List[UserDTO],
        page: int,
        total_count: int,
    ) -> InlineKeyboardMarkup:
        return remove_user_inline_kb(
            users=items,
            page=page,
            total_count=total_count,
        )


remove_users_handler = RemoveUsersPaginationHandler()


@router.callback_query(
    UserStateManager.removing_user,
    F.data.startswith(CallbackData.User.PREFIX_PREV_REMOVE_USERS_PAGE),
)
async def prev_page_remove_users_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик перехода на предыдущую страницу для удаления пользователей"""
    await remove_users_handler.handle_prev_page(callback, state, container)


@router.callback_query(
    UserStateManager.removing_user,
    F.data.startswith(CallbackData.User.PREFIX_NEXT_REMOVE_USERS_PAGE),
)
async def next_page_remove_users_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик перехода на следующую страницу для удаления пользователей"""
    await remove_users_handler.handle_next_page(callback, state, container)
