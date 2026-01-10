import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants.pagination import CATEGORIES_PAGE_SIZE
from keyboards.inline.categories import categories_inline_ikb
from keyboards.inline.templates import templates_menu_ikb
from services.categories import CategoryService
from states import TemplateStateManager
from utils.send_message import safe_edit_message

logger = logging.getLogger(__name__)


router = Router(name=__name__)


@router.callback_query(
    F.data == "select_category",
)
async def select_category_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    await callback.answer()

    try:
        category_service: CategoryService = container.resolve(CategoryService)
        categories = await category_service.get_categories()

        if not categories:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="❗ Категорий не найдено",
                reply_markup=templates_menu_ikb(),
            )
            return

        first_page_categories = categories[:CATEGORIES_PAGE_SIZE]

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="Выберите категорию.",
            reply_markup=categories_inline_ikb(
                categories=first_page_categories,
                page=1,
                total_count=len(categories),
            ),
        )

        await state.set_state(TemplateStateManager.listing_categories)
    except Exception as e:
        logger.error("Ошибка при получении категорий: %s", e, exc_info=True)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="Произошла ошибка при получении категорий.",
            reply_markup=templates_menu_ikb(),
        )
        return
