import logging
from typing import List, Tuple

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from constants.pagination import USERS_PAGE_SIZE
from dto.user import UserDTO
from keyboards.inline.users import users_inline_kb, users_menu_ikb
from states import UserStateManager
from usecases.user_tracking import GetListTrackedUsersUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


async def get_tracked_users(admin_tgid: str, container: Container) -> List[UserDTO]:
    """Получает всех отслеживаемых пользователей для администратора."""
    usecase: GetListTrackedUsersUseCase = container.resolve(GetListTrackedUsersUseCase)
    return await usecase.execute(admin_tgid=admin_tgid)


def paginate_users(
    users: List[UserDTO],
    page: int,
    page_size: int = USERS_PAGE_SIZE,
) -> Tuple[List[UserDTO], int]:
    """Разбивает список пользователей на страницы."""
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    return users[start_idx:end_idx], len(users)


async def _display_tracked_users_page(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
    page: int = 1,
) -> None:
    """Вспомогательная функция для отображения страницы списка пользователей."""
    admin_tgid = callback.from_user.id
    admin_username = callback.from_user.username or "неизвестно"

    try:
        users = await get_tracked_users(str(admin_tgid), container)

        if not users:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=Dialog.User.EMPTY_TRACKED_LIST,
                reply_markup=users_menu_ikb(has_tracked_users=False),
            )
            return

        page_users, total_count = paginate_users(users, page)

        if not page_users and page > 1:
            # Если страница пуста (например, после удаления), показываем предыдущую
            await _display_tracked_users_page(callback, state, container, page - 1)
            return

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.User.LIST_TRACKED_USERS,
            reply_markup=users_inline_kb(
                users=page_users,
                page=page,
                total_count=total_count,
            ),
        )
        await state.set_state(UserStateManager.listing_users)

    except Exception as e:
        logger.error(
            "Ошибка при отображении списка пользователей для админа tg_id:%d username:%s: %s",
            admin_tgid,
            admin_username,
            e,
            exc_info=True,
        )
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.User.ERROR_GET_TRACKED_USERS,
            reply_markup=users_menu_ikb(has_tracked_users=False),
        )


@router.callback_query(F.data == CallbackData.User.SHOW_TRACKED_USERS_LIST)
async def users_list_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик команды для отображения списка пользователей."""
    await callback.answer()
    await state.clear()

    logger.info(
        "Администратор tg_id:%d username:%s запросил список пользователей",
        callback.from_user.id,
        callback.from_user.username or "неизвестно",
    )
    await _display_tracked_users_page(callback, state, container, page=1)


@router.callback_query(
    UserStateManager.listing_users,
    F.data.startswith(CallbackData.User.PREFIX_PREV_USERS_PAGE),
)
async def prev_page_users_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик перехода на предыдущую страницу пользователей."""
    await callback.answer()
    current_page = int(callback.data.split("__")[1])
    prev_page = max(1, current_page - 1)
    await _display_tracked_users_page(callback, state, container, page=prev_page)


@router.callback_query(
    UserStateManager.listing_users,
    F.data.startswith(CallbackData.User.PREFIX_NEXT_USERS_PAGE),
)
async def next_page_users_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик перехода на следующую страницу пользователей."""
    await callback.answer()
    current_page = int(callback.data.split("__")[1])
    next_page = current_page + 1
    await _display_tracked_users_page(callback, state, container, page=next_page)
