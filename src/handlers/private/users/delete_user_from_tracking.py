import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import KbCommands
from constants.pagination import USERS_PAGE_SIZE
from container import container
from dto import RemoveUserTrackingDTO
from keyboards.inline.users import conf_remove_user_kb, remove_user_inline_kb
from keyboards.reply.menu import user_menu_kb
from states import MenuStates
from usecases.user import GetUserByIdUseCase
from usecases.user_tracking import (
    GetListTrackedUsersUseCase,
    RemoveUserFromTrackingUseCase,
)
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(
    F.text == KbCommands.REMOVE_USER,
    MenuStates.users_menu,
)
async def remove_user_from_tracking_handler(message: Message) -> None:
    """
    Обработчик для удаления пользователя из списка отслеживания.
    """
    try:
        logger.info(
            f"Пользователь {message.from_user.id} запросил список пользователей для удаления"
        )

        usecase: GetListTrackedUsersUseCase = container.resolve(
            GetListTrackedUsersUseCase
        )
        tracked_users = await usecase.execute(admin_tgid=str(message.from_user.id))

        if not tracked_users:
            logger.info("Список пользователей пуст")
            message_text = (
                "⚠ Удаление невозможно, так как в отслеживание "
                "ещё не добавлен ни один пользователь."
            )
            await send_html_message_with_kb(
                message=message,
                text=message_text,
                reply_markup=user_menu_kb(),
            )
            return

        logger.info(f"Найдено {len(tracked_users)} пользователей для удаления")

        # Показываем первую страницу
        first_page_users = tracked_users[:USERS_PAGE_SIZE]

        await send_html_message_with_kb(
            message=message,
            text=f"Всего {len(tracked_users)} пользователей",
            reply_markup=remove_user_inline_kb(
                users=first_page_users,
                page=1,
                total_count=len(tracked_users),
            ),
        )
    except Exception as e:
        await handle_exception(
            message=message,
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

        use_case: GetUserByIdUseCase = container.resolve(GetUserByIdUseCase)
        user = await use_case.execute(user_id=user_id)

        if not user:
            logger.warning(f"Пользователь с ID {user_id} не найден")
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        await state.update_data(user_id=user_id)
        logger.info(f"Запрос подтверждения удаления пользователя: {user.username}")

        message_text = (
            f"❗Вы уверены, что хотите удалить @{user.username} из отслеживаемых?"
        )

        await send_html_message_with_kb(
            message=callback.message,
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
                logger.info(f"Пользователь ID {user_id} успешно удален из отслеживания")
                text = (
                    f"✅ Готово! Пользователь удалён из отлеживания!\n\n"
                    "❗️Вы всегда можете вернуть пользователя "
                    "в отслеживаемые и продолжить собирать статистику"
                )
            else:
                logger.warning(f"Не удалось удалить пользователя ID {user_id}")
                text = f"❌ Пользователь не найден или уже удален."

            await callback.message.edit_text(text=text)
        else:
            logger.info(f"Удаление пользователя ID {user_id} отменено")
            await callback.message.edit_text(
                text=f"❌ Удаление из отслеживания отменено!",
            )
    except Exception as e:
        await handle_exception(callback.message, e, "confirmation_removing_user")
    finally:
        await callback.answer()
        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=MenuStates.users_menu,
        )
