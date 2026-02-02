from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from punq import Container

from constants import Dialog
from keyboards.inline.menu import main_menu_ikb
from services.user import UserService

router = Router(name=__name__)


@router.message(CommandStart())
async def start_handler(
    message: Message, container: Container, user_language: str
) -> None:
    """
    Выводит приветственное сообщение
    """
    user_service: UserService = container.resolve(UserService)
    user = await user_service.get_user(tg_id=str(message.from_user.id))

    await message.answer(
        text=Dialog.Menu.MENU_TEXT.format(username=user.username),
        reply_markup=main_menu_ikb(
            user=user,
            user_language=user_language,
        ),
    )
