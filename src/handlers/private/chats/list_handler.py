from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from container import container
from keyboards.inline.chats_kb import chats_inline_kb
from states import ChatStateManager
from usecases.chat import GetAllChatsUseCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.message(F.text == KbCommands.SELECT_CHAT)
async def chats_list_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды для получения списка чатов.
    """

    try:
        # Состояние вывода списка чатов
        await state.set_state(ChatStateManager.listing_chats)

        username = message.from_user.username

        # Получение чатов из БД
        usecase: GetAllChatsUseCase = container.resolve(GetAllChatsUseCase)
        chats = await usecase.execute(username)

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
