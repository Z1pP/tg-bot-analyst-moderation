import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants.pagination import TEMPLATES_PAGE_SIZE
from dto.template_dto import GetTemplatesByScopeDTO
from keyboards.inline.templates import templates_inline_kb, templates_menu_ikb
from states import TemplateStateManager
from exceptions.base import BotBaseException
from handlers._handler_errors import raise_business_logic
from usecases.templates import GetTemplatesByScopeUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == "template_scope_global",
    TemplateStateManager.selecting_template_scope,
)
async def select_global_templates_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик выбора глобальных шаблонов"""
    await callback.answer()

    try:
        usecase: GetTemplatesByScopeUseCase = container.resolve(
            GetTemplatesByScopeUseCase
        )
        templates, total_count = await usecase.execute(
            GetTemplatesByScopeDTO(scope="global", page=1, page_size=TEMPLATES_PAGE_SIZE)
        )

        if not templates:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="❗ Глобальных шаблонов не найдено",
                reply_markup=templates_menu_ikb(),
            )
            await state.set_state(TemplateStateManager.templates_menu)
            return

        await state.update_data(template_scope="global")

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"Глобальные шаблоны ({total_count}):",
            reply_markup=templates_inline_kb(
                templates=templates,
                page=1,
                total_count=total_count,
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
        raise_business_logic(
            "Ошибка в select_global_templates_handler.",
            "❌ Произошла ошибка при получении глобальных шаблонов.",
            e,
            logger,
        )


@router.callback_query(
    F.data.startswith("template_scope_chat__"),
    TemplateStateManager.selecting_template_scope,
)
async def select_chat_templates_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик выбора шаблонов для конкретного чата"""
    await callback.answer()

    chat_id = int(callback.data.split("__")[1])

    try:
        usecase: GetTemplatesByScopeUseCase = container.resolve(
            GetTemplatesByScopeUseCase
        )
        templates, total_count = await usecase.execute(
            GetTemplatesByScopeDTO(
                scope="chat", chat_id=chat_id, page=1, page_size=TEMPLATES_PAGE_SIZE
            )
        )

        if not templates:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="❗ Шаблонов для этого чата не найдено",
                reply_markup=templates_menu_ikb(),
            )
            await state.set_state(TemplateStateManager.templates_menu)
            return

        await state.update_data(template_scope="chat", chat_id=chat_id)

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"Шаблоны для чата ({total_count}):",
            reply_markup=templates_inline_kb(
                templates=templates,
                page=1,
                total_count=total_count,
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
        raise_business_logic(
            "Ошибка в select_chat_templates_handler.",
            "❌ Произошла ошибка при получении шаблонов чата.",
            e,
            logger,
        )
