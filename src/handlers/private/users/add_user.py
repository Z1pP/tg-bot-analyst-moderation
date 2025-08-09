import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import Dialog, KbCommands
from container import container
from keyboards.reply import admin_menu_kb, get_back_kb
from states import MenuStates
from states.user_states import UsernameManagement
from usecases.user import GetOrCreateUserIfNotExistUserCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state
from utils.username_validator import validate_username

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
            f"Пользователь {message.from_user.id} начал добавление нового пользователя"
        )

        await log_and_set_state(
            message=message,
            state=state,
            new_state=UsernameManagement.imput_username,
        )

        await send_html_message_with_kb(
            message=message,
            text=Dialog.INPUT_MODERATOR_USERNAME,
            reply_markup=get_back_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "add_user_to_tracking_handler")


@router.message(UsernameManagement.imput_username)
async def process_adding_user(message: Message, state: FSMContext) -> None:
    """
    Обработчик для получения @username нового пользователя.
    """
    try:
        admin_username = message.from_user.username or "Неизвестно"
        logger.info(f"Обработка добавления пользователя от {admin_username}")

        if message.text == KbCommands.BACK:
            await back_to_menu_handler(message, state)
            return

        if message.forward_from:
            username = (
                message.forward_from.username or f"user_{message.forward_from.id}"
            )
            user_id = str(message.forward_from.id)
            logger.info(f"Получено пересланное сообщение от пользователя: {username}")
        else:
            username = validate_username(message.text)
            user_id = "Неизвестно"
            logger.info(f"Получен username из текста: {username}")

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

        use_case: GetOrCreateUserIfNotExistUserCase = container.resolve(
            GetOrCreateUserIfNotExistUserCase
        )
        user = await use_case.execute(username=username)

        if user.is_existed:
            logger.info(f"Пользователь {username} уже существует в системе")
            await send_html_message_with_kb(
                message=message,
                text=Dialog.Error.ADD_USER_ERROR.format(
                    problem=Dialog.Error.USER_ALREADY_TRACKED,
                    solution=Dialog.Error.SOLUTION_USER_EXISTS,
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
    except Exception as e:
        await handle_exception(message, e, "process_adding_user")
    finally:
        await state.clear()


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
