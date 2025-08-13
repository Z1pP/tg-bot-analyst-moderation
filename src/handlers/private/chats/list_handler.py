from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from container import container
from keyboards.inline.chats_kb import chats_inline_kb
from keyboards.reply import chat_menu_kb
from states import ChatStateManager, MenuStates
from usecases.chat import GetAllChatsUseCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state

router = Router(name=__name__)


@router.message(
    F.text == KbCommands.GET_STATISTICS,
    MenuStates.chats_menu,
)
async def chats_list_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды для получения списка чатов.
    """

    try:
        username = message.from_user.username

        # Получение чатов из БД
        usecase: GetAllChatsUseCase = container.resolve(GetAllChatsUseCase)
        chats = await usecase.execute(username)

        if not chats:
            message_text = (
                "❗Чтобы получать отчёты по чату, необходимо добавить чат "
                "в отслеживаемые, а также пользователей для сбора статистики"
            )
            await send_html_message_with_kb(
                message=message,
                text=message_text,
                reply_markup=chat_menu_kb(),
            )
            return

        await log_and_set_state(
            message=message,
            state=state,
            new_state=ChatStateManager.listing_chats,
        )

        await send_html_message_with_kb(
            message=message,
            text=f"Найдено {len(chats)} чат(-ов):",
            reply_markup=chats_inline_kb(chats=chats),
        )
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="chats_list_handler",
        )
