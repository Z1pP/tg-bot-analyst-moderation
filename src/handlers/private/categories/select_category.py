import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants.pagination import CATEGORIES_PAGE_SIZE
from container import container
from keyboards.inline.categories import categories_inline_ikb
from keyboards.inline.chats_kb import template_scope_selector_ikb
from keyboards.inline.templates import templates_inline_kb, templates_menu_ikb
from services.categories import CategoryService
from services.templates import TemplateService
from states import TemplateStateManager
from usecases.chat import GetTrackedChatsUseCase
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    TemplateStateManager.process_template_category,
    F.data.startswith("category__"),
)
async def select_category_for_template_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик выбора категории при создании нового шаблона"""
    await callback.answer()

    category_id = int(callback.data.split("__")[1])
    username = callback.from_user.username

    logger.info(
        "Была выбрана категория id=%s пользователем - %s",
        category_id,
        username,
    )

    await state.update_data(category_id=category_id)

    try:
        usecase: GetTrackedChatsUseCase = container.resolve(GetTrackedChatsUseCase)
        chats = await usecase.execute(tg_id=str(callback.from_user.id))
        await callback.message.edit_text(
            text="Выбери группу для шаблона:",
            reply_markup=template_scope_selector_ikb(chats=chats),
        )

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=TemplateStateManager.process_template_chat,
        )
    except Exception as e:
        logger.error("Ошибка при получении списка чатов чатов: %s", e, exc_info=True)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ Ошибка при получении списка чатов",
            reply_markup=templates_menu_ikb(),
        )


@router.callback_query(
    TemplateStateManager.listing_categories,
    F.data.startswith("category__"),
)
async def show_templates_by_category_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик выбора категории при просмотре шаблонов"""
    await callback.answer()

    category_id = int(callback.data.split("__")[1])

    logger.info(
        "Была выбрана категория id=%s пользователем - %s",
        category_id,
        callback.from_user.username,
    )

    await state.update_data(category_id=category_id)

    try:
        service: TemplateService = container.resolve(TemplateService)
        templates = await service.get_by_category(category_id=category_id)
        total_count = await service.get_count_by_category(category_id=category_id)

        await callback.message.edit_text(
            text="Выберите шаблон:",
            reply_markup=templates_inline_kb(
                templates=templates,
                page=1,
                total_count=total_count,
                show_back_to_categories=True,
            ),
        )

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=TemplateStateManager.listing_templates,
        )
    except Exception as e:
        logger.error("Ошибка при получении шаблонов: %s", e)
        # Пытаемся вернуться к списку категорий
        try:
            category_service: CategoryService = container.resolve(CategoryService)
            categories = await category_service.get_categories()
            if categories:
                first_page_categories = categories[:CATEGORIES_PAGE_SIZE]
                await safe_edit_message(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text="❌ Ошибка при получении шаблонов. Выберите категорию:",
                    reply_markup=categories_inline_ikb(
                        categories=first_page_categories,
                        page=1,
                        total_count=len(categories),
                    ),
                )
                await log_and_set_state(
                    message=callback.message,
                    state=state,
                    new_state=TemplateStateManager.listing_categories,
                )
            else:
                await safe_edit_message(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text="❌ Ошибка при получении шаблонов",
                    reply_markup=templates_menu_ikb(),
                )
        except Exception as inner_e:
            logger.error("Ошибка при возврате к категориям: %s", inner_e)
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="❌ Ошибка при получении шаблонов",
                reply_markup=templates_menu_ikb(),
            )
