from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import KbCommands
from container import container
from keyboards.inline.moderators import conf_remove_user_kb, remove_inline_kb
from keyboards.reply.menu import admin_menu_kb, moderator_menu_kb
from usecases.user import (
    DeleteUserUseCase,
    GetAllUsersUseCase,
    GetUserByIdUseCase,
)
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.message(F.text == KbCommands.REMOVE_USER)
async def remove_moderator_handler(message: Message) -> None:
    """
    Обработчик команды для получения списка модераторов.
    """

    try:
        usecase: GetAllUsersUseCase = container.resolve(GetAllUsersUseCase)

        users = await usecase.execute()

        if not users:
            await send_html_message_with_kb(
                message=message,
                text="Список модераторов пуст. Добавьте модераторов",
                reply_markup=admin_menu_kb(),
            )
            return

        await send_html_message_with_kb(
            message=message,
            text=f"Всего {len(users)} модераторов",
            reply_markup=remove_inline_kb(users),
        )
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="moderators_list_handler",
        )


@router.callback_query(F.data.startswith("remove_user__"))
async def process_removing_moderator(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик для удаления модератора.
    """
    user_id = int(callback.data.split("__")[1])
    try:
        use_case: GetUserByIdUseCase = container.resolve(GetUserByIdUseCase)
        user = await use_case.execute(user_id=user_id)

        await state.update_data(user_id=user_id, username=user.username)

        message_text = (
            f"❗Вы уверены, что хотите удалить @{user.username} из отслеживаемых?"
        )

        await send_html_message_with_kb(
            message=callback.message,
            text=message_text,
            reply_markup=conf_remove_user_kb(),
        )
    except Exception as e:
        await handle_exception(callback.message, e, "process_removing_moderator")
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
    data = await state.get_data()
    user_id = data.get("user_id")
    username = data.get("username")

    try:
        answer = callback.data.split("__")[1]

        if answer == "yes":
            delete_usecase: DeleteUserUseCase = container.resolve(DeleteUserUseCase)
            success = await delete_usecase.execute(user_id=user_id)

            if success:
                text = (
                    f"✅ Готово! @{username} удалён из отлеживания!\n\n"
                    "❗️Вы всегда можете вернуть пользователя "
                    "в отслеживаемые и продолжить собирать статистику"
                )
            else:
                text = f"❌ Пользователь @{username} не найден или уже удален."

            await callback.message.edit_text(text=text)
        else:
            await callback.message.edit_text(
                text=f"❌ Удаление @{username} отменено!",
            )
    except Exception as e:
        await handle_exception(callback.message, e, "confirmation_removing_user")
    finally:
        await callback.answer()
        await state.clear()
