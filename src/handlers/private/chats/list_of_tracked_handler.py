import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from constants.pagination import CHATS_PAGE_SIZE
from container import container
from keyboards.inline.chats_kb import tracked_chats_inline_kb
from keyboards.reply import chat_menu_kb
from states import MenuStates
from states.chat_states import ChatStateManager
from usecases.chat import GetTrackedChatsUseCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.message(F.text == KbCommands.GET_STATISTICS, MenuStates.chats_menu)
@router.message(F.text == KbCommands.SELECT_CHAT)
async def list_of_tracking_chats_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды для получения списка трекающих чатов.
    """
    try:
        tg_id = str(message.from_user.id)

        usecase: GetTrackedChatsUseCase = container.resolve(GetTrackedChatsUseCase)
        chats = await usecase.execute(tg_id=tg_id)

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
            new_state=ChatStateManager.listing_tracking_chats,
        )
        # Показываем первую страницу
        first_page_chats = chats[:CHATS_PAGE_SIZE]

        # Отправляем сообщение с кнопками для выбора действия
        await send_html_message_with_kb(
            message=message,
            text=f"Найдено {len(chats)} чат(-ов):",
            reply_markup=tracked_chats_inline_kb(
                chats=first_page_chats,
                page=1,
                total_count=len(chats),
            ),
        )
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="list_of_tracking_chats_handler",
        )
