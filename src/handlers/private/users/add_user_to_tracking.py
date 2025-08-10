import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import Dialog, KbCommands
from container import container
from keyboards.reply import admin_menu_kb, get_back_kb
from states import MenuStates
from states.user_states import UsernameStates
from usecases.user_tracking import AddUserToTrackingUseCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state
from utils.username_validator import parse_and_validate_username

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(
    F.text == KbCommands.ADD_USER,
    MenuStates.users_menu,
)
async def add_user_to_tracking_handler(message: Message, state: FSMContext) -> None:
    """
    Хендлер для обработки добавления пользователя в список отслеживания.
    """
    try:
        logger.info(
            f"Пользователь {message.from_user.id} начал добавление "
            "нового пользователя в отслеживание"
        )

        await log_and_set_state(
            message=message,
            state=state,
            new_state=UsernameStates.waiting_username_input,
        )

        await send_html_message_with_kb(
            message=message,
            text=Dialog.INPUT_MODERATOR_USERNAME,
            reply_markup=get_back_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "add_user_to_tracking_handler")


@router.message(UsernameStates.waiting_username_input)
async def process_adding_user(message: Message, state: FSMContext) -> None:
    """
    Обработчик для получения @username нового пользователя.
    """
    try:
        admin_username = message.from_user.username
        logger.info(f"Обработка добавления пользователя от {admin_username}")

        if message.text == KbCommands.BACK:
            await back_to_menu_handler(message, state)
            return

        if message.forward_from:
            username = message.forward_from.username
            user_id = message.forward_from.id
        elif message.text.strip().startswith("@"):
            username = parse_and_validate_username(text=message.text)
            user_id = "Неизвестно"
        else:
            await send_html_message_with_kb(
                message=message,
                text=Dialog.Error.ADD_USER_ERROR.format(
                    problem=Dialog.Error.USER_IS_HIDDEN,
                    solution=Dialog.Error.SOLUTION_USER_IS_HIDDEN,
                ),
            )
            return

        if not username:
            logger.warning(f"Неверный формат username: {message.text}")
            await send_html_message_with_kb(
                message=message,
                text=Dialog.Error.ADD_USER_ERROR.format(
                    problem="неверный формат username",
                    solution=Dialog.Error.SOLUTION_CHECK_USERNAME,
                ),
            )
            return

        use_case: AddUserToTrackingUseCase = container.resolve(AddUserToTrackingUseCase)
        is_success = await use_case.execute(
            admin_username=admin_username,
            user_username=username,
        )

        if not is_success:
            logger.info(f"Ошибка добавления пользователя {username} в отслеживание")
            await send_html_message_with_kb(
                message=message,
                text=Dialog.Error.ADD_USER_ERROR.format(
                    problem="Ошибка добавления пользователя в отслеживание",
                    solution="Попробуйте еще раз",
                ),
                reply_markup=admin_menu_kb(),
            )
            return

        logger.info(
            f"Пользователь {username} успешно добавлен администратором {admin_username}"
        )
        await send_html_message_with_kb(
            message=message,
            text=Dialog.SUCCESS_ADD_MODERATOR.format(
                forward_username=username,
                forward_user_id=user_id,
                admin_username=admin_username,
            ),
            reply_markup=admin_menu_kb(),
        )

        await log_and_set_state(
            message=message,
            state=state,
            new_state=MenuStates.users_menu,
        )
    except Exception as e:
        await handle_exception(message, e, "process_adding_user")


async def back_to_menu_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик для возврата в главное меню.
    """
    try:
        logger.info(f"Пользователь {message.from_user.id} возвращается в главное меню")

        await log_and_set_state(
            message=message,
            state=state,
            new_state=MenuStates.main_menu,
        )

        await send_html_message_with_kb(
            message=message,
            text="Возвращаемся в главное меню",
            reply_markup=admin_menu_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "back_to_menu_handler")
