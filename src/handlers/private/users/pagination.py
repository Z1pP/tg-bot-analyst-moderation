from typing import List, Tuple

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from constants.callback import CallbackData
from constants.pagination import USERS_PAGE_SIZE
from container import container
from keyboards.inline.users import remove_user_inline_kb, users_inline_kb
from models import User
from states import UserStateManager
from usecases.user_tracking import GetListTrackedUsersUseCase
from utils.pagination_handler import BasePaginationHandler

router = Router(name=__name__)


class UsersPaginationHandler(BasePaginationHandler):
    def __init__(self):
        super().__init__("пользователей")

    async def get_page_data(
        self,
        page: int,
        query: CallbackQuery,
        state: FSMContext,
    ) -> Tuple[List[User], int]:
        users = await get_tracked_users(str(query.from_user.id))
        return paginate_users(users, page)

    async def build_keyboard(
        self,
        items: List[User],
        page: int,
        total_count: int,
    ) -> InlineKeyboardMarkup:
        return users_inline_kb(
            users=items,
            page=page,
            total_count=total_count,
        )


class RemoveUsersPaginationHandler(BasePaginationHandler):
    def __init__(self):
        super().__init__("пользователей")

    async def get_page_data(
        self,
        page: int,
        query: CallbackQuery,
        state: FSMContext,
    ) -> Tuple[List[User], int]:
        users = await get_tracked_users(str(query.from_user.id))
        return paginate_users(users, page)

    async def build_keyboard(
        self,
        items: List[User],
        page: int,
        total_count: int,
    ) -> InlineKeyboardMarkup:
        return remove_user_inline_kb(
            users=items,
            page=page,
            total_count=total_count,
        )


users_handler = UsersPaginationHandler()
remove_users_handler = RemoveUsersPaginationHandler()


@router.callback_query(
    UserStateManager.listing_users,
    F.data.startswith(CallbackData.User.PREFIX_PREV_USERS_PAGE),
)
async def prev_page_users_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик перехода на предыдущую страницу пользователей"""
    await users_handler.handle_prev_page(callback, state)


@router.callback_query(
    UserStateManager.listing_users,
    F.data.startswith(CallbackData.User.PREFIX_NEXT_USERS_PAGE),
)
async def next_page_users_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик перехода на следующую страницу пользователей"""
    await users_handler.handle_next_page(callback, state)


@router.callback_query(
    UserStateManager.removing_user,
    F.data.startswith(CallbackData.User.PREFIX_PREV_REMOVE_USERS_PAGE),
)
async def prev_page_remove_users_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик перехода на предыдущую страницу для удаления пользователей"""
    await remove_users_handler.handle_prev_page(callback, state)


@router.callback_query(
    UserStateManager.removing_user,
    F.data.startswith(CallbackData.User.PREFIX_NEXT_REMOVE_USERS_PAGE),
)
async def next_page_remove_users_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик перехода на следующую страницу для удаления пользователей"""
    await remove_users_handler.handle_next_page(callback, state)


async def get_tracked_users(admin_tgid: str) -> List[User]:
    """Получает всех отслеживаемых пользователей для администратора."""
    usecase: GetListTrackedUsersUseCase = container.resolve(GetListTrackedUsersUseCase)
    return await usecase.execute(admin_tgid=admin_tgid)


def paginate_users(
    users: List[User],
    page: int,
    page_size: int = USERS_PAGE_SIZE,
) -> Tuple[List[User], int]:
    """Разбивает список пользователей на страницы."""
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    return users[start_idx:end_idx], len(users)
