from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from container import container
from keyboards.inline.templates_answers import templates_inline_kb
from keyboards.reply.menu import tamplates_menu_kb
from repositories import QuickResponseRepository
from states import QuickResponseStateManager
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.message(F.text == KbCommands.SELECT_TEMPLATE)
async def templates_list_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды для получения списка шаблонов сообщений.
    """

    try:
        # Состояние вывода списка чатов
        await state.set_state(QuickResponseStateManager.listing_templates)

        # Получение всех шаблонов из БД
        # TODO: Декомпозировать по сервисам и юзкейсам
        response_repo: QuickResponseRepository = container.resolve(
            QuickResponseRepository
        )
        templates = await response_repo.get_all_quick_responses()

        if not templates:
            await send_html_message_with_kb(
                message=message,
                text="Список шаблонов пуст. Добавьте шаблон",
                reply_markup=tamplates_menu_kb(),
            )
            return

        await send_html_message_with_kb(
            message=message,
            text=f"Всего {len(templates)} шаблонов",
            reply_markup=templates_inline_kb(templates=templates),
        )
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="templates_list_handler",
        )
