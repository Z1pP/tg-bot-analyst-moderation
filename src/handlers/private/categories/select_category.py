import logging
from typing import Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants.pagination import CATEGORIES_PAGE_SIZE
from dto.template_dto import GetTemplatesByCategoryDTO
from exceptions.base import BotBaseException
from handlers._handler_errors import raise_business_logic
from keyboards.inline.categories import categories_inline_ikb
from keyboards.inline.chats import template_scope_selector_ikb
from keyboards.inline.templates import templates_inline_kb, templates_menu_ikb
from states import TemplateStateManager
from usecases.categories import GetCategoriesUseCase
from usecases.chat import GetTrackedChatsUseCase
from usecases.templates import GetTemplatesByCategoryUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


def _parse_category_id(callback_data: str) -> Optional[int]:
    """Извлекает и валидирует category_id из callback_data формата 'category__{id}'."""
    try:
        raw = callback_data.split("__")[1]
        value = int(raw)
        return value if value > 0 else None
    except (IndexError, ValueError):
        return None


@router.callback_query(
    TemplateStateManager.process_template_category,
    F.data.startswith("category__"),
)
async def select_category_for_template_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик выбора категории при создании нового шаблона"""
    await callback.answer()

    category_id = _parse_category_id(callback.data or "")
    if category_id is None:
        logger.warning("Некорректный callback_data для категории: %s", callback.data)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ Некорректный запрос. Выберите категорию из списка.",
            reply_markup=templates_menu_ikb(),
        )
        return

    logger.info(
        "Была выбрана категория id=%s пользователем - %s",
        category_id,
        callback.from_user.username,
    )

    await state.update_data(category_id=category_id)

    try:
        usecase: GetTrackedChatsUseCase = container.resolve(GetTrackedChatsUseCase)
        chats = await usecase.execute(tg_id=str(callback.from_user.id))
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="Выбери группу для шаблона:",
            reply_markup=template_scope_selector_ikb(chats=chats),
        )

        await state.set_state(TemplateStateManager.process_template_chat)
    except BotBaseException as e:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=e.get_user_message(),
            reply_markup=templates_menu_ikb(),
        )
    except Exception as e:
        raise_business_logic(
            "Ошибка при получении списка чатов.",
            "Произошла ошибка при получении списка чатов.",
            e,
            logger,
        )


@router.callback_query(
    TemplateStateManager.listing_categories,
    F.data.startswith("category__"),
)
async def show_templates_by_category_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик выбора категории при просмотре шаблонов"""
    await callback.answer()

    category_id = _parse_category_id(callback.data or "")
    if category_id is None:
        logger.warning("Некорректный callback_data для категории: %s", callback.data)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ Некорректный запрос. Выберите категорию из списка.",
            reply_markup=templates_menu_ikb(),
        )
        return

    logger.info(
        "Была выбрана категория id=%s пользователем - %s",
        category_id,
        callback.from_user.username,
    )

    await state.update_data(category_id=category_id)

    try:
        usecase: GetTemplatesByCategoryUseCase = container.resolve(
            GetTemplatesByCategoryUseCase
        )
        templates, total_count = await usecase.execute(
            GetTemplatesByCategoryDTO(category_id=category_id, page=1)
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="Выберите шаблон:",
            reply_markup=templates_inline_kb(
                templates=templates,
                page=1,
                total_count=total_count,
                show_back_to_categories=True,
            ),
        )

        await state.set_state(TemplateStateManager.listing_templates)
    except BotBaseException as e:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=e.get_user_message(),
            reply_markup=templates_menu_ikb(),
        )
    except Exception as e:
        logger.exception("Ошибка при получении шаблонов: %s", e)
        try:
            get_categories_uc: GetCategoriesUseCase = container.resolve(
                GetCategoriesUseCase
            )
            categories = await get_categories_uc.execute()
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
                await state.set_state(TemplateStateManager.listing_categories)
            else:
                await safe_edit_message(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text="❌ Ошибка при получении шаблонов",
                    reply_markup=templates_menu_ikb(),
                )
        except Exception as inner_e:
            raise_business_logic(
                "Ошибка при возврате к категориям.",
                "Произошла ошибка при получении шаблонов.",
                inner_e,
                logger,
            )
