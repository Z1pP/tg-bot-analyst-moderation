import logging

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import CommandList
from container import container
from states import AddModeratorState, RemoveModeratorState
from usecases.user import DeleteUserUseCase, GetOrCreateUserIfNotExistUserCase
from utils.username_validator import validate_username

router = Router(name=__name__)

logger = logging.getLogger(__name__)


@router.message(Command(CommandList.ADD_MODERATOR.name.lower()))
async def add_moderator_handler(message: Message, state: FSMContext):
    """
    Хендлер для команды добавления модератора.
    Запрашивает username нового модератора.
    """
    await state.clear()

    await message.answer(
        text="Введите <b>username</b> пользователя",
        parse_mode=ParseMode.HTML,
    )
    await state.set_state(AddModeratorState.waiting_for_username)


@router.message(AddModeratorState.waiting_for_username, F.text)
async def process_adding_moderator(message: Message, state: FSMContext):
    """
    Обработчик для добавления нового модератора.
    Проверяет username и создает/получает пользователя.
    """
    use_case: GetOrCreateUserIfNotExistUserCase = container.resolve(
        GetOrCreateUserIfNotExistUserCase
    )
    username = await validate_username(text=message.text)

    if not username:
        await message.answer(
            "Некорректно введен username! Формат: @username или username"
        )
        return

    try:
        user = await use_case.execute(username=username)
        await message.answer(
            text=f"Пользователь <b>{user.username}</b> добавлен в список модераторов",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error("An unforeseen mistake occurred: %s", str(e))
        await message.answer("Ошибка при добавлении пользователя")


@router.message(Command(CommandList.REMOVE_MODERATOR.name.lower()))
async def remove_moderator_handler(message: Message, state: FSMContext):
    """
    Хендлер для команды удаления модератора.
    Запрашивает username модератора для удаления.
    """
    await state.clear()

    await message.answer(
        text="Введите <b>username</b> модератора",
        parse_mode=ParseMode.HTML,
    )
    await state.set_state(RemoveModeratorState.waiting_for_username)


@router.message(RemoveModeratorState.waiting_for_username, F.text)
async def process_removing_moderator(message: Message, state: FSMContext):
    """
    Обработчик для удаления модератора.
    Проверяет username и удаляет пользователя.
    """
    use_case: DeleteUserUseCase = container.resolve(DeleteUserUseCase)
    username = await validate_username(text=message.text)

    if not username:
        await message.answer(
            "Некорректно введен username! Формат: @username или username"
        )
        return

    try:
        await use_case.execute(username=username)
        await message.answer(
            text=f"Пользователь <b>{username}</b> удален из списка модераторов",
            parse_mode=ParseMode.HTML,
        )
    except ValueError as e:
        await message.answer(str(e))
    except Exception as e:
        logger.error("An unforeseen mistake occurred: %s", str(e))
        await message.answer("Ошибка при удалении пользователя")
