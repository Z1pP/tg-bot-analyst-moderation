from typing import List

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from container import container
from dto.user import UserDTO
from keyboards.inline.users import users_inline_kb
from usecases.user_tracking import GetListTrackedUsersUseCase

router = Router(name=__name__)


@router.callback_query(F.data.startswith("prev_users_page__"))
async def prev_users_page_callback(query: CallbackQuery, state: FSMContext) -> None:
    """Обработчик перехода на предыдущую страницу пользователей"""
    current_page = int(query.data.split("__")[1])
    prev_page = max(1, current_page - 1)
    
    users = await get_tracked_users(query.from_user.username)
    users_page, total_count = paginate_users(users, prev_page)
    
    await query.message.edit_reply_markup(
        reply_markup=users_inline_kb(
            users=users_page,
            page=prev_page,
            total_count=total_count,
        )
    )
    await query.answer()


@router.callback_query(F.data.startswith("next_users_page__"))
async def next_users_page_callback(query: CallbackQuery, state: FSMContext) -> None:
    """Обработчик перехода на следующую страницу пользователей"""
    current_page = int(query.data.split("__")[1])
    next_page = current_page + 1
    
    users = await get_tracked_users(query.from_user.username)
    users_page, total_count = paginate_users(users, next_page)
    
    if not users_page:
        await query.answer("Больше пользователей нет")
        return
    
    await query.message.edit_reply_markup(
        reply_markup=users_inline_kb(
            users=users_page,
            page=next_page,
            total_count=total_count,
        )
    )
    await query.answer()


async def get_tracked_users(admin_username: str) -> List[UserDTO]:
    """Получает всех отслеживаемых пользователей."""
    usecase: GetListTrackedUsersUseCase = container.resolve(GetListTrackedUsersUseCase)
    return await usecase.execute(admin_username=admin_username)


def paginate_users(users: List[UserDTO], page: int, page_size: int = 5) -> tuple[List[UserDTO], int]:
    """Разбивает список пользователей на страницы."""
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    return users[start_idx:end_idx], len(users)