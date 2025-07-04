from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from container import container
from keyboards.inline.categories import categories_inline_kb
from repositories import QuickResponseCategoryRepository
from states import QuickResponseStateManager
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.message(F.text == KbCommands.SELECT_CATEGORY)
async def list_categories_handler(message: Message, state: FSMContext):
    """Выводит список категорий полученных из БД"""

    await state.set_state(QuickResponseStateManager.listing_categories)

    repo: QuickResponseCategoryRepository = container.resolve(
        QuickResponseCategoryRepository
    )

    try:
        categories = await repo.get_all_categories()

        await send_html_message_with_kb(
            message=message,
            text="Выберите категорию:",
            reply_markup=categories_inline_kb(categories=categories),
        )
    except Exception as e:
        await handle_exception(
            message=message, exc=e, context="list_categories_handler"
        )
