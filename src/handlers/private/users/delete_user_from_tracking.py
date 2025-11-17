import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants.pagination import USERS_PAGE_SIZE
from container import container
from dto import RemoveUserTrackingDTO
from keyboards.inline.users import (
    conf_remove_user_kb,
    remove_user_inline_kb,
    users_menu_ikb,
)
from states import UserStateManager
from usecases.user import GetUserByIdUseCase
from usecases.user_tracking import (
    GetListTrackedUsersUseCase,
    RemoveUserFromTrackingUseCase,
)
from utils.exception_handler import handle_exception
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "remove_user")
async def remove_user_from_tracking_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """
    Обработчик для удаления пользователя из списка отслеживания.
    """
    await callback.answer()
    await state.clear()

    try:
        logger.info(
            f"Пользователь {callback.from_user.id} запросил список пользователей для удаления"
        )

        usecase: GetListTrackedUsersUseCase = container.resolve(
            GetListTrackedUsersUseCase
        )
        tracked_users = await usecase.execute(admin_tgid=str(callback.from_user.id))

        if not tracked_users:
            logger.info("Список пользователей пуст")
            message_text = (
                "⚠ Удаление невозможно, так как в отслеживание "
                "ещё не добавлен ни один пользователь."
            )
            await callback.message.edit_text(
                text=message_text,
                reply_markup=users_menu_ikb(),
            )
            return

        logger.info(f"Найдено {len(tracked_users)} пользователей для удаления")

        # Показываем первую страницу
        first_page_users = tracked_users[:USERS_PAGE_SIZE]

        await callback.message.edit_text(
            text=f"Всего {len(tracked_users)} пользователей",
            reply_markup=remove_user_inline_kb(
                users=first_page_users,
                page=1,
                total_count=len(tracked_users),
            ),
        )

        await state.update_data(current_page=1)
        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=UserStateManager.removing_user,
        )
    except Exception as e:
        await handle_exception(
            message=callback.message,
            exc=e,
            context="remove_user_from_tracking_handler",
        )


@router.callback_query(F.data.startswith("remove_user__"))
async def process_removing_user(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик для получения ID выбранного пользователя на удаление.
    """
    try:
        user_id = int(callback.data.split("__")[1])
        logger.info(f"Запрос на удаление пользователя с ID: {user_id}")

        # Сохраняем текущую страницу из state (если есть)
        data = await state.get_data()
        current_page = data.get("current_page", 1)

        use_case: GetUserByIdUseCase = container.resolve(GetUserByIdUseCase)
        user = await use_case.execute(user_id=user_id)

        if not user:
            logger.warning(f"Пользователь с ID {user_id} не найден среди отслеживаемых")
            await callback.answer(
                "Пользователь не найден среди отслеживаемых", show_alert=True
            )
            return

        await state.update_data(
            user_id=user_id, user_username=user.username, current_page=current_page
        )
        logger.info(f"Запрос подтверждения удаления пользователя: {user.username}")

        message_text = (
            f"❗Вы уверены, что хотите удалить @{user.username} из отслеживаемых?"
        )

        await callback.message.edit_text(
            text=message_text,
            reply_markup=conf_remove_user_kb(),
        )
    except Exception as e:
        await handle_exception(callback.message, e, "process_removing_user")
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("conf_remove_user__"))
async def confirmation_removing_user(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик подтверждения удаления пользователя из отслеживания
    """
    try:
        data = await state.get_data()
        user_id = data.get("user_id")
        current_page = data.get("current_page", 1)
        answer = callback.data.split("__")[1]

        logger.info(f"Подтверждение удаления пользователя ID {user_id}: {answer}")

        if answer == "yes":
            dto = RemoveUserTrackingDTO(
                admin_username=callback.from_user.username,
                admin_tgid=str(callback.from_user.id),
                user_id=user_id,
            )

            usecase: RemoveUserFromTrackingUseCase = container.resolve(
                RemoveUserFromTrackingUseCase
            )
            success = await usecase.execute(dto=dto)

            if success:
                user_username = data.get("user_username", "")
                logger.info(f"Пользователь ID {user_id} успешно удален из отслеживания")
                text = (
                    f"✅ Готово! Пользователь @{user_username} удалён из отлеживания!\n\n"
                    "❗️Вы всегда можете вернуть пользователя "
                    "в отслеживаемые и продолжить собирать статистику"
                )
                await callback.message.edit_text(
                    text=text,
                    reply_markup=users_menu_ikb(),
                )
            else:
                logger.warning(f"Не удалось удалить пользователя ID {user_id}")
                text = "❌ Пользователь не найден среди отслеживаемых или уже удален."
                await callback.message.edit_text(
                    text=text,
                    reply_markup=users_menu_ikb(),
                )

            await log_and_set_state(
                message=callback.message,
                state=state,
                new_state=UserStateManager.users_menu,
            )
        else:
            # Отмена - возвращаемся к списку пользователей для удаления
            logger.info(f"Удаление пользователя ID {user_id} отменено")

            usecase: GetListTrackedUsersUseCase = container.resolve(
                GetListTrackedUsersUseCase
            )
            tracked_users = await usecase.execute(admin_tgid=str(callback.from_user.id))

            if not tracked_users:
                await callback.message.edit_text(
                    text="⚠ Удаление невозможно, так как в отслеживание "
                    "ещё не добавлен ни один пользователь.",
                    reply_markup=users_menu_ikb(),
                )
                await log_and_set_state(
                    message=callback.message,
                    state=state,
                    new_state=UserStateManager.users_menu,
                )
                return

            total_count = len(tracked_users)
            max_pages = (total_count + USERS_PAGE_SIZE - 1) // USERS_PAGE_SIZE
            page = min(current_page, max_pages) if max_pages > 0 else 1

            start_index = (page - 1) * USERS_PAGE_SIZE
            end_index = start_index + USERS_PAGE_SIZE
            page_users = tracked_users[start_index:end_index]

            await callback.message.edit_text(
                text=f"Всего {total_count} пользователей",
                reply_markup=remove_user_inline_kb(
                    users=page_users,
                    page=page,
                    total_count=total_count,
                ),
            )
            await state.update_data(current_page=page)
            await log_and_set_state(
                message=callback.message,
                state=state,
                new_state=UserStateManager.removing_user,
            )
    except Exception as e:
        await handle_exception(callback.message, e, "confirmation_removing_user")
    finally:
        await callback.answer()
