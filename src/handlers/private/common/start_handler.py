from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from punq import Container

from constants import Dialog
from keyboards.inline.menu import main_menu_ikb
from usecases.user import GetUserByTgIdUseCase

router = Router(name=__name__)


@router.message(CommandStart())
async def start_handler(
    message: Message, container: Container, user_language: str
) -> None:
    """
    Выводит приветственное сообщение
    """
    usecase: GetUserByTgIdUseCase = container.resolve(GetUserByTgIdUseCase)
    user = await usecase.execute(tg_id=str(message.from_user.id))
    if not user:
        await message.answer(text=Dialog.User.ERROR_GET_USER)
        return

    await message.answer(
        text=Dialog.Menu.MENU_TEXT.format(username=user.username),
        reply_markup=main_menu_ikb(
            user=user,
            user_language=user_language,
        ),
    )
