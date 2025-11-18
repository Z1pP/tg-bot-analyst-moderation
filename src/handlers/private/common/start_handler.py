from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from constants import Dialog
from constants.i18n import DEFAULT_LANGUAGE
from container import container
from keyboards.inline.menu import admin_menu_ikb
from services.user import UserService

router = Router(name=__name__)


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """
    Выводит приветственное сообщение
    """
    username = message.from_user.full_name
    welcome_text = Dialog.MENU_TEXT.format(username=username)

    # Получаем язык пользователя из БД (LanguageMiddleware уже сохранил его)
    user_service: UserService = container.resolve(UserService)
    db_user = await user_service.get_user(tg_id=str(message.from_user.id))
    user_language = (
        db_user.language if db_user and db_user.language else DEFAULT_LANGUAGE
    )

    await message.answer(
        text=welcome_text,
        reply_markup=admin_menu_ikb(user_language),
    )
