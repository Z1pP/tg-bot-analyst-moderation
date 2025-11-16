from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants.pagination import USERS_PAGE_SIZE
from container import container
from keyboards.inline.users import users_inline_kb
from states import UserStateManager
from usecases.user_tracking import GetListTrackedUsersUseCase

router = Router(name=__name__)


@router.callback_query(
    UserStateManager.listing_users,
    F.data.startswith("prev_users_page__"),
)
async def prev_page_users_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик перехода на предыдущую страницу пользователей"""
    current_page = int(callback.data.split("__")[1])
    prev_page = max(1, current_page - 1)

    usecase: GetListTrackedUsersUseCase = container.resolve(GetListTrackedUsersUseCase)
    users = await usecase.execute(admin_tgid=str(callback.from_user.id))

    if not users:
        await callback.answer("Нет пользователей для отображения", show_alert=True)
        return

    total_count = len(users)
    start_index = (prev_page - 1) * USERS_PAGE_SIZE
    end_index = start_index + USERS_PAGE_SIZE
    page_users = users[start_index:end_index]

    await callback.message.edit_reply_markup(
        reply_markup=users_inline_kb(
            users=page_users,
            page=prev_page,
            total_count=total_count,
        )
    )
    await callback.answer()


@router.callback_query(
    UserStateManager.listing_users,
    F.data.startswith("next_users_page__"),
)
async def next_page_users_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик перехода на следующую страницу пользователей"""
    current_page = int(callback.data.split("__")[1])
    next_page = current_page + 1

    usecase: GetListTrackedUsersUseCase = container.resolve(GetListTrackedUsersUseCase)
    users = await usecase.execute(admin_tgid=str(callback.from_user.id))

    if not users:
        await callback.answer("Нет пользователей для отображения", show_alert=True)
        return

    total_count = len(users)
    max_pages = (total_count + USERS_PAGE_SIZE - 1) // USERS_PAGE_SIZE

    if next_page > max_pages:
        await callback.answer("ℹ️ Больше пользователей нет")
        return

    start_index = (next_page - 1) * USERS_PAGE_SIZE
    end_index = start_index + USERS_PAGE_SIZE
    page_users = users[start_index:end_index]

    await callback.message.edit_reply_markup(
        reply_markup=users_inline_kb(
            users=page_users,
            page=next_page,
            total_count=total_count,
        )
    )
    await callback.answer()


@router.callback_query(
    UserStateManager.removing_user,
    F.data.startswith("prev_remove_users_page__"),
)
async def prev_page_remove_users_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик перехода на предыдущую страницу для удаления пользователей"""
    current_page = int(callback.data.split("__")[1])
    prev_page = max(1, current_page - 1)

    from keyboards.inline.users import remove_user_inline_kb

    usecase: GetListTrackedUsersUseCase = container.resolve(GetListTrackedUsersUseCase)
    users = await usecase.execute(admin_tgid=str(callback.from_user.id))

    if not users:
        await callback.answer("Нет пользователей для отображения", show_alert=True)
        return

    total_count = len(users)
    start_index = (prev_page - 1) * USERS_PAGE_SIZE
    end_index = start_index + USERS_PAGE_SIZE
    page_users = users[start_index:end_index]

    await callback.message.edit_reply_markup(
        reply_markup=remove_user_inline_kb(
            users=page_users,
            page=prev_page,
            total_count=total_count,
        )
    )
    await state.update_data(current_page=prev_page)
    await callback.answer()


@router.callback_query(
    UserStateManager.removing_user,
    F.data.startswith("next_remove_users_page__"),
)
async def next_page_remove_users_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик перехода на следующую страницу для удаления пользователей"""
    current_page = int(callback.data.split("__")[1])
    next_page = current_page + 1

    from keyboards.inline.users import remove_user_inline_kb

    usecase: GetListTrackedUsersUseCase = container.resolve(GetListTrackedUsersUseCase)
    users = await usecase.execute(admin_tgid=str(callback.from_user.id))

    if not users:
        await callback.answer("Нет пользователей для отображения", show_alert=True)
        return

    total_count = len(users)
    max_pages = (total_count + USERS_PAGE_SIZE - 1) // USERS_PAGE_SIZE

    if next_page > max_pages:
        await callback.answer("ℹ️ Больше пользователей нет")
        return

    start_index = (next_page - 1) * USERS_PAGE_SIZE
    end_index = start_index + USERS_PAGE_SIZE
    page_users = users[start_index:end_index]

    await callback.message.edit_reply_markup(
        reply_markup=remove_user_inline_kb(
            users=page_users,
            page=next_page,
            total_count=total_count,
        )
    )
    await state.update_data(current_page=next_page)
    await callback.answer()
