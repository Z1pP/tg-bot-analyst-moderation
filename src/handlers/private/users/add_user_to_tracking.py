import logging
from dataclasses import dataclass

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import Dialog, KbCommands
from container import container
from dto import UserTrackingDTO
from keyboards.reply import get_back_kb, user_menu_kb
from states import MenuStates
from states.user_states import UsernameStates
from usecases.user_tracking import AddUserToTrackingUseCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state
from utils.user_data_parser import parse_data_from_text

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedData:
    username: str
    user_tgid: str


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
            new_state=UsernameStates.waiting_user_data_input,
        )

        await send_html_message_with_kb(
            message=message,
            text=Dialog.INPUT_MODERATOR_USERNAME,
            reply_markup=get_back_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "add_user_to_tracking_handler")


@router.message(UsernameStates.waiting_user_data_input)
async def process_adding_user(message: Message, state: FSMContext) -> None:
    """
    Обработчик для получения @username и ID пользователя.
    """
    try:
        admin_username = message.from_user.username
        logger.info(f"Обработка добавления пользователя от {admin_username}")

        if message.text == KbCommands.BACK:
            await back_to_user_menu_handler(message, state)
            return

        try:
            user_data = parse_data_from_text(text=message.text)
        except ValueError:
            await send_html_message_with_kb(
                message=message,
                text=Dialog.Error.INVALID_USERNAME_FORMAT,
            )
            return

        if user_data is None:
            text = "❗Неверный формат ввода. Попробуйте еще раз."
            await message.reply(text=text)
            return

        tracking_dto = UserTrackingDTO(
            admin_username=admin_username,
            admin_tgid=str(message.from_user.id),
            user_username=user_data.username,
            user_tgid=user_data.tg_id,
        )

        usecase: AddUserToTrackingUseCase = container.resolve(AddUserToTrackingUseCase)
        result = await usecase.execute(dto=tracking_dto)

        if not result.success:
            logger.info(
                f"Ошибка добавления пользователя {user_data.username} в отслеживание"
            )
            await send_html_message_with_kb(
                message=message,
                text=result.message,
                reply_markup=user_menu_kb(),
            )
            return

        logger.info(
            f"Пользователь {user_data.username} успешно добавлен администратором {admin_username}"
        )
        await send_html_message_with_kb(
            message=message,
            text=result.message,
            reply_markup=user_menu_kb(),
        )

        await log_and_set_state(
            message=message,
            state=state,
            new_state=MenuStates.users_menu,
        )
    except Exception as e:
        await handle_exception(message, e, "process_adding_user")


async def back_to_user_menu_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик для возврата в меню управления пользователями.
    """
    try:
        logger.info(f"Пользователь {message.from_user.id} возвращается в главное меню")

        await log_and_set_state(
            message=message,
            state=state,
            new_state=MenuStates.users_menu,
        )

        await send_html_message_with_kb(
            message=message,
            text="Возвращаемся в главное меню",
            reply_markup=user_menu_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "back_to_menu_handler")
