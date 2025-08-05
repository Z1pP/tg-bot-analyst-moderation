from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import Dialog, KbCommands
from container import container
from keyboards.reply import admin_menu_kb, get_back_kb
from states.user_states import UsernameManagement
from usecases.user import GetOrCreateUserIfNotExistUserCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.username_validator import validate_username

router = Router(name=__name__)


@router.message(F.text == KbCommands.ADD_MODERATOR)
async def add_moderator_handler(message: Message, state: FSMContext) -> None:
    """
    Хендлер для команды добавления модератора.
    """
    await state.set_state(UsernameManagement.imput_username)

    await send_html_message_with_kb(
        message=message,
        text=Dialog.INPUT_MODERATOR_USERNAME,
        reply_markup=get_back_kb(),
    )


@router.message(UsernameManagement.imput_username)
async def process_adding_moderator(message: Message, state: FSMContext) -> None:
    """
    Обработчик для добавления нового модератора.
    """

    admin_username = message.from_user.username

    if message.text == KbCommands.BACK:
        await back_to_menu_handler(message, state)
        return

    if message.forward_from:
        username = message.forward_from.username
        user_id = str(message.forward_from.id)
    else:
        username = validate_username(message.text)
        user_id = "Неизвестно"

    if not username:
        await send_html_message_with_kb(
            message=message,
            text=Dialog.Error.ADD_USER_ERROR.format(
                problem="неверный формат username",
                solution=Dialog.Error.SOLUTION_CHECK_USERNAME,
            ),
        )
        return

    try:
        use_case: GetOrCreateUserIfNotExistUserCase = container.resolve(
            GetOrCreateUserIfNotExistUserCase
        )
        user = await use_case.execute(username=username)

        if user.is_existed:
            await send_html_message_with_kb(
                message=message,
                text=Dialog.Error.ADD_USER_ERROR.format(
                    problem=Dialog.Error.USER_ALREADY_TRACKED,
                    solution=Dialog.Error.SOLUTION_USER_EXISTS,
                ),
                reply_markup=admin_menu_kb(),
            )
            return

        await send_html_message_with_kb(
            message=message,
            text=Dialog.SUCCESS_ADD_MODERATOR.format(
                forward_username=username,
                forward_user_id=user_id,
                admin_username=admin_username,
            ),
            reply_markup=admin_menu_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "process_adding_moderator")
    finally:
        await state.clear()


async def back_to_menu_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик для возврата в главное меню.
    """
    await state.clear()

    await send_html_message_with_kb(
        message=message,
        text="Нет так нет.",
        reply_markup=admin_menu_kb(),
    )
