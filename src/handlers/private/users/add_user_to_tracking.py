import logging
from dataclasses import dataclass
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import Dialog, KbCommands
from container import container
from keyboards.reply import get_back_kb, user_menu_kb
from states import MenuStates
from states.user_states import UsernameStates
from usecases.user_tracking import AddUserToTrackingUseCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state
from utils.username_validator import parse_and_validate_username

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
            parse_data = parse_data_from_text(text=message.text)
        except ValueError:
            await send_html_message_with_kb(
                message=message,
                text=Dialog.Error.INVALID_USERNAME_FORMAT,
            )
            return

        chat_user_data = await find_user_in_chats(
            bot=message.bot,
            user_id=parse_data.user_tgid,
        )

        actual_username = (
            chat_user_data.username if chat_user_data else parse_data.username
        )
        actual_tg_id = (
            chat_user_data.user_tgid if chat_user_data else parse_data.user_tgid
        )

        # Получаем/обновляем/создаем пользователя в БД
        user_data = await get_or_update_user(
            username=actual_username,
            tg_id=actual_tg_id,
        )

        usecase: AddUserToTrackingUseCase = container.resolve(AddUserToTrackingUseCase)
        is_success = await usecase.execute(
            admin_username=admin_username,
            user_username=user_data.username,
        )

        if not is_success:
            logger.info(
                f"Ошибка добавления пользователя {user_data.username} в отслеживание"
            )
            await send_html_message_with_kb(
                message=message,
                text=Dialog.Error.ADD_USER_ERROR.format(
                    problem="Ошибка добавления пользователя в отслеживание",
                    solution="Попробуйте еще раз",
                ),
                reply_markup=user_menu_kb(),
            )
            return

        logger.info(
            f"Пользователь {user_data.username} успешно добавлен администратором {admin_username}"
        )
        await send_html_message_with_kb(
            message=message,
            text=Dialog.SUCCESS_ADD_MODERATOR.format(
                forward_username=user_data.username,
                forward_user_id=user_data.user_tgid,
                admin_username=admin_username,
            ),
            reply_markup=user_menu_kb(),
        )

        await log_and_set_state(
            message=message,
            state=state,
            new_state=MenuStates.users_menu,
        )
    except Exception as e:
        await handle_exception(message, e, "process_adding_user")


async def get_or_update_user(username: str, tg_id: str):
    from repositories import UserRepository

    user_repo: UserRepository = container.resolve(UserRepository)

    # Ищем по tg_id
    user = await user_repo.get_user_by_tg_id(tg_id=tg_id)
    if user:
        # Если username отличаются - обновляем username
        if user.username != username:
            user = await user_repo.update_username(
                user_id=user.id,
                new_username=username,
            )
        return ParsedData(
            username=user.username,
            user_tgid=str(user.tg_id),
        )

    # Ищем по username
    user = await user_repo.get_user_by_username(username=username)
    if user:
        # Если нет tg_id - добавляем
        if not user.tg_id:
            user = await user_repo.update_tg_id(
                user_id=user.id,
                new_tg_id=tg_id,
            )
        return ParsedData(
            username=user.username,
            user_tgid=str(user.tg_id),
        )

    user = await user_repo.create_user(
        username=username,
        tg_id=tg_id,
    )
    return ParsedData(username=user.username, user_tgid=str(user.tg_id))


async def find_user_in_chats(bot: Bot, user_id: str) -> Optional[ParsedData]:
    from repositories import ChatRepository

    chat_repo: ChatRepository = container.resolve(ChatRepository)
    chats = await chat_repo.get_all()

    for chat in chats:
        try:
            member = await bot.get_chat_member(
                chat_id=chat.chat_id,
                user_id=int(user_id),
            )
            if member.user:
                return ParsedData(
                    username=member.user.username,
                    user_tgid=str(member.user.id),
                )
        except Exception:
            continue
    return None


def parse_data_from_text(text: str) -> ParsedData:
    """Парсит username и user_tgid из текста, разделенного \n"""
    lines = text.strip().split("\n")

    if len(lines) != 2:
        raise ValueError("Ожидается 2 строки: username и user_id")

    username = parse_and_validate_username(lines[0])
    user_tgid = lines[1].strip()

    if not username:
        raise ValueError("Неверный формат username")

    return ParsedData(username=username, user_tgid=user_tgid)


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
