import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from container import container
from keyboards.inline.templates import conf_remove_template_kb, templates_menu_ikb
from states import TemplateStateManager
from usecases.templates import DeleteTemplateUseCase
from utils.state_logger import log_and_set_state

router = Router(name=__name__)

logger = logging.getLogger(__name__)


@router.callback_query(
    F.data.startswith("remove_template__"),
    TemplateStateManager.listing_templates,
)
async def remove_template_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Обработчик начала удаления шаблона"""
    await callback.answer()

    template_id = int(callback.data.split("__")[1])

    logger.info(
        "Пользователь %s запросил удаление шаблона ID: %d",
        callback.from_user.full_name,
        template_id,
    )

    await state.update_data(template_id=int(template_id))

    await callback.message.edit_text(
        text="Вы уверены, что хотите удалить шаблон?",
        reply_markup=conf_remove_template_kb(),
    )


@router.callback_query(
    F.data.startswith("conf_remove_template__"),
    TemplateStateManager.removing_template,
)
async def confirmation_removing_template_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    answer = callback.data.split("__")[1]
    data = await state.get_data()
    template_id = data.get("template_id")

    if answer != "yes":
        await callback.message.edit_text(
            text="❌ Удаление отменено",
            reply_markup=templates_menu_ikb(),
        )
        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=TemplateStateManager.templates_menu,
        )
        return

    try:
        usecase: DeleteTemplateUseCase = container.resolve(DeleteTemplateUseCase)
        await usecase.execute(template_id=template_id)

        await callback.message.edit_text(
            text="✅ Шаблон успешно удален",
            reply_markup=templates_menu_ikb(),
        )
        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=TemplateStateManager.templates_menu,
        )
    except Exception as e:
        logger.error("Ошибка при удалении шаблона: %s", e, exc_info=True)
        await callback.message.edit_text(
            "⚠️ Произошла ошибка при удалении",
            reply_markup=templates_menu_ikb(),
        )
        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=TemplateStateManager.templates_menu,
        )
