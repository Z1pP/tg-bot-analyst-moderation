import logging

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from constants import CommandList
from container import container
from usecases.user import DeleteUserUseCase, GetOrCreateUserIfNotExistUserCase
from utils.username_validator import validate_username

router = Router(name=__name__)
logger = logging.getLogger(__name__)


def extract_username(text: str) -> str | None:
    """
    Извлекает username из текста команды.
    """
    segments = text.split(" ")
    if len(segments) > 1:
        username = segments[-1].strip()
        return username if username.startswith("@") else f"@{username}"
    return None


async def get_valid_username(message: Message) -> str | None:
    """
    Извлекает и валидирует username из сообщения.
    """
    username = extract_username(message.text)
    if username is None:
        await message.answer(
            text=(
                "Некорректно введена команда! \n"
                "Формат: <code>/add_moderator @username</code>"
            ),
            parse_mode=ParseMode.HTML,
        )
        return None

    username = await validate_username(username=username)
    if username is None:
        await message.answer(
            text="Указан некорректный username. Проверьте формат и попробуйте снова.",
            parse_mode=ParseMode.HTML,
        )
        return None

    return username


async def handle_error(message: Message, error: Exception, action: str):
    """
    Обрабатывает ошибки и отправляет сообщение пользователю.
    """
    logger.error("An error occurred during %s: %s", action, str(error))
    await message.answer(f"Ошибка при {action}. Попробуйте позже.")


@router.message(Command(CommandList.ADD_MODERATOR.name.lower()))
async def add_moderator_handler(message: Message):
    """
    Хендлер для команды добавления модератора.
    """
    username = await get_valid_username(message)
    if username is None:
        return

    await process_adding_moderator(username=username, message=message)


async def process_adding_moderator(username: str, message: Message):
    """
    Обработчик для добавления нового модератора.
    """
    use_case: GetOrCreateUserIfNotExistUserCase = container.resolve(
        GetOrCreateUserIfNotExistUserCase
    )

    try:
        user = await use_case.execute(username=username)

        if user.is_existed:
            await message.answer(
                text=f"Пользователь <b>{username}</b> уже является модератором",
                parse_mode=ParseMode.HTML,
            )
            return

        await message.answer(
            text=f"Пользователь <b>{username}</b> добавлен в список модераторов",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await handle_error(message, e, "добавлении модератора")


@router.message(Command(CommandList.REMOVE_MODERATOR.name.lower()))
async def remove_moderator_handler(message: Message):
    """
    Хендлер для команды удаления модератора.
    """
    username = await get_valid_username(message)
    if username is None:
        return

    await process_removing_moderator(username=username, message=message)


async def process_removing_moderator(username: str, message: Message):
    """
    Обработчик для удаления модератора.
    """
    use_case: DeleteUserUseCase = container.resolve(DeleteUserUseCase)

    try:
        await use_case.execute(username=username)
        await message.answer(
            text=f"Пользователь <b>{username}</b> удален из списка модераторов",
            parse_mode=ParseMode.HTML,
        )
    except ValueError as e:
        await message.answer(str(e))
    except Exception as e:
        await handle_error(message, e, "удалении модератора")
