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
from keyboards.inline.users import (
    back_to_users_menu_ikb,
    show_tracked_users_ikb,
    users_menu_ikb,
)
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

        # Формируем текстовый список пользователей
        lines = [Dialog.User.LIST_TRACKED_USERS, ""]
        for i, user in enumerate(users, 1):
            user_ident = (
                f"@{user.username}"
                if user.username
                else f"ID: <code>{user.tg_id}</code>"
            )
            added_date = (
                user.added_at.strftime("%d.%m.%Y") if user.added_at else "неизвестно"
            )
            lines.append(f"{i}. {user_ident} - доб. {added_date}")

        message_text = "\n".join(lines)

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=message_text,
            reply_markup=back_to_users_menu_ikb(),
        )

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
async def show_users_list_handler(
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


@router.callback_query(F.data == CallbackData.User.SELECT_USER)
async def select_user_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик команды для отображения списка пользователей через inline клавиатуру"""
    await callback.answer()

    logger.info(
        "Администратор tg_id:%d username:%s запросил список пользователей для отчета",
        callback.from_user.id,
        callback.from_user.username or "неизвестно",
    )

    usecase: GetListTrackedUsersUseCase = container.resolve(GetListTrackedUsersUseCase)
    users = await usecase.execute(admin_tgid=str(callback.from_user.id))

    if not users:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Analytics.NO_TRACKED_USERS,
            reply_markup=users_menu_ikb(has_tracked_users=False),
        )
        return

    logger.info(
        "Найдено %d пользователей для отчета для администратора tg_id:%d username:%s",
        len(users),
        callback.from_user.id,
        callback.from_user.username or "неизвестно",
    )

    # Показываем первую страницу
    first_page_users = users[:USERS_PAGE_SIZE]

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Analytics.TOTAL_USERS.format(total=len(users)),
        reply_markup=show_tracked_users_ikb(
            users=first_page_users,
            page=1,
            total_count=len(users),
        ),
    )
