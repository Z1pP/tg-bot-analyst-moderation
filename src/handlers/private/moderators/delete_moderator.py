from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import KbCommands
from container import container
from keyboards.inline.moderators import remove_inline_kb
from keyboards.reply.menu import get_admin_menu_kb
from usecases.user import DeleteUserUseCase, GetAllUsersUseCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.message(F.text == KbCommands.REMOVE_MODERATOR)
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
                reply_markup=get_admin_menu_kb(),
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
    callback: CallbackQuery, state: FSMContext
) -> None:
    """
    Обработчик для удаления модератора.
    """
    username = callback.data.split("__")[1]

    use_case: DeleteUserUseCase = container.resolve(DeleteUserUseCase)

    try:
        await callback.answer()

        await use_case.execute(username=username)
        await send_html_message_with_kb(
            message=callback.message,
            text=f"Пользователь <b>{username}</b> удален из списка модераторов",
        )
    except Exception as e:
        await handle_exception(callback.message, e, "удалении модератора")
    finally:
        await state.clear()
