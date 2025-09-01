from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from constants.pagination import CATEGORIES_PAGE_SIZE
from container import container
from keyboards.inline.categories import categories_inline_kb
from repositories import TemplateCategoryRepository
from states import TemplateStateManager
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.message(F.text == KbCommands.SELECT_CATEGORY)
async def list_categories_handler(message: Message, state: FSMContext):
    """Выводит список категорий полученных из БД"""

    await state.set_state(TemplateStateManager.listing_categories)

    repo: TemplateCategoryRepository = container.resolve(TemplateCategoryRepository)

    try:
        # Получаем первую страницу категорий
        categories = await repo.get_categories_paginated(
            limit=CATEGORIES_PAGE_SIZE,
            offset=0,
        )
        total_count = await repo.get_categories_count()

        await send_html_message_with_kb(
            message=message,
            text=f"Выберите категорию (всего {total_count}):",
            reply_markup=categories_inline_kb(
                categories=categories,
                page=1,
                total_count=total_count,
            ),
        )
    except Exception as e:
        await handle_exception(
            message=message, exc=e, context="list_categories_handler"
        )
