from typing import List, Tuple

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from constants.pagination import USERS_PAGE_SIZE
from container import container
from dto.user import UserDTO
from keyboards.inline.users import remove_user_inline_kb, users_inline_kb
from usecases.user_tracking import GetListTrackedUsersUseCase
from utils.pagination_handler import BasePaginationHandler

router = Router(name=__name__)


class UsersPaginationHandler(BasePaginationHandler):
    def __init__(self):
        super().__init__("пользователей")

    async def get_page_data(
        self,
        page: int,
        callback: CallbackQuery,
        state: FSMContext,
    ) -> Tuple[List[UserDTO], int]:
        users = await get_tracked_users(callback.from_user.username)
        users_page, total_count = paginate_users(users, page)
        return users_page, total_count

    async def build_keyboard(
        self, items: List[UserDTO], page: int, total_count: int
    ) -> InlineKeyboardMarkup:
        return users_inline_kb(users=items, page=page, total_count=total_count)


class RemoveUsersPaginationHandler(BasePaginationHandler):
    def __init__(self):
        super().__init__("пользователей")

    async def get_page_data(
        self,
        page: int,
        callback: CallbackQuery,
        state: FSMContext,
    ) -> Tuple[List[UserDTO], int]:
        users = await get_tracked_users(callback.from_user.username)
        users_page, total_count = paginate_users(users, page)
        return users_page, total_count

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


users_handler = UsersPaginationHandler()
remove_users_handler = RemoveUsersPaginationHandler()


@router.callback_query(F.data.startswith("prev_users_page__"))
async def prev_users_page_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await users_handler.handle_prev_page(callback, state)


@router.callback_query(F.data.startswith("next_users_page__"))
async def next_users_page_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await users_handler.handle_next_page(callback, state)


@router.callback_query(F.data.startswith("prev_remove_users_page__"))
async def prev_remove_users_page_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await remove_users_handler.handle_prev_page(callback, state)


@router.callback_query(F.data.startswith("next_remove_users_page__"))
async def next_remove_users_page_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await remove_users_handler.handle_next_page(callback, state)


async def get_tracked_users(admin_username: str) -> List[UserDTO]:
    """Получает всех отслеживаемых пользователей."""
    usecase: GetListTrackedUsersUseCase = container.resolve(GetListTrackedUsersUseCase)
    return await usecase.execute(admin_username=admin_username)


def paginate_users(
    users: List[UserDTO], page: int, page_size: int = USERS_PAGE_SIZE
) -> tuple[List[UserDTO], int]:
    """Разбивает список пользователей на страницы."""
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    return users[start_idx:end_idx], len(users)


@router.callback_query(F.data.startswith("prev_remove_users_page__"))
async def prev_remove_users_page_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик перехода на предыдущую страницу удаления пользователей"""
    from keyboards.inline.users import remove_user_inline_kb

    current_page = int(callback.data.split("__")[1])
    prev_page = max(1, current_page - 1)

    users = await get_tracked_users(callback.from_user.username)
    users_page, total_count = paginate_users(users, prev_page)

    await callback.message.edit_reply_markup(
        reply_markup=remove_user_inline_kb(
            users=users_page,
            page=prev_page,
            total_count=total_count,
        )
    )
    await callback.answer()


@router.callback_query(F.data.startswith("next_remove_users_page__"))
async def next_remove_users_page_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик перехода на следующую страницу удаления пользователей"""
    from keyboards.inline.users import remove_user_inline_kb

    current_page = int(callback.data.split("__")[1])
    next_page = current_page + 1

    users = await get_tracked_users(callback.from_user.username)
    users_page, total_count = paginate_users(users, next_page)

    if not users_page:
        await callback.answer("Больше пользователей нет")
        return

    await callback.message.edit_reply_markup(
        reply_markup=remove_user_inline_kb(
            users=users_page,
            page=next_page,
            total_count=total_count,
        )
    )
    await callback.answer()
