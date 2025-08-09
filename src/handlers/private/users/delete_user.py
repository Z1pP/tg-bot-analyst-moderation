import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import KbCommands
from container import container
from keyboards.inline.moderators import conf_remove_user_kb, remove_inline_kb
from keyboards.reply.menu import admin_menu_kb
from states import MenuStates
from usecases.user import (
    DeleteUserUseCase,
    GetAllUsersUseCase,
    GetUserByIdUseCase,
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

        usecase: GetAllUsersUseCase = container.resolve(GetAllUsersUseCase)
        users = await usecase.execute()

        if not users:
            logger.info("Список пользователей пуст")
            message_text = (
                "❗Чтобы получать отчёты по пользователям, "
                "необходимо добавить юзера в отслеживаемые, "
                "а также пользователей для сбора статистики"
            )
            await send_html_message_with_kb(
                message=message,
                text=message_text,
                reply_markup=admin_menu_kb(),
            )
            return

        logger.info(f"Найдено {len(users)} пользователей для удаления")
        await send_html_message_with_kb(
            message=message,
            text=f"Всего {len(users)} пользователей",
            reply_markup=remove_inline_kb(users),
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

        await state.update_data(user_id=user_id, username=user.username)
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
        username = data.get("username")
        answer = callback.data.split("__")[1]

        logger.info(f"Подтверждение удаления пользователя {username}: {answer}")

        if answer == "yes":
            delete_usecase: DeleteUserUseCase = container.resolve(DeleteUserUseCase)
            success = await delete_usecase.execute(user_id=user_id)

            if success:
                logger.info(f"Пользователь {username} успешно удален")
                text = (
                    f"✅ Готово! @{username} удалён из отлеживания!\n\n"
                    "❗️Вы всегда можете вернуть пользователя "
                    "в отслеживаемые и продолжить собирать статистику"
                )
            else:
                logger.warning(f"Не удалось удалить пользователя {username}")
                text = f"❌ Пользователь @{username} не найден или уже удален."

            await callback.message.edit_text(text=text)
        else:
            logger.info(f"Удаление пользователя {username} отменено")
            await callback.message.edit_text(
                text=f"❌ Удаление @{username} отменено!",
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
