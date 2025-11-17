import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from constants.pagination import CHATS_PAGE_SIZE
from container import container
from keyboards.inline.chats_kb import chats_menu_ikb, tracked_chats_ikb
from states import MenuStates
from states.chat_states import ChatStateManager
from usecases.chat import GetTrackedChatsUseCase
from utils.exception_handler import handle_exception
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
            await message.answer(
                text=message_text,
                reply_markup=chats_menu_ikb(),
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
        await message.answer(
            text=f"Найдено {len(chats)} чат(-ов):",
            reply_markup=tracked_chats_ikb(
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
