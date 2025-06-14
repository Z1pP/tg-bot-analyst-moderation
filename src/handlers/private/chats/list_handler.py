from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from container import container
from keyboards.inline.chats_kb import chats_inline_kb
from keyboards.reply.menu import admin_menu_kb
from states import ChatStateManager
from usecases.chat import GetAllChatsUseCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.message(F.text == KbCommands.SELECT_CHAT)
async def chats_list_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды для получения списка модераторов.
    """

    try:
        # Состояние вывода списка чатов
        await state.set_state(ChatStateManager.listing_chats)

        username = message.from_user.username

        # Получение чатов из БД
        usecase: GetAllChatsUseCase = container.resolve(GetAllChatsUseCase)
        chats = await usecase.execute(username)

        if not chats:
            await send_html_message_with_kb(
                message=message,
                text="Список чатов пуст. Добавьте бот в чат и выдайте ему админ права",
                reply_markup=admin_menu_kb(),
            )
            return

        await send_html_message_with_kb(
            message=message,
            text=f"Всего {len(chats)} чатов",
            reply_markup=chats_inline_kb(chats=chats),
        )
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="chats_list_handler",
        )
