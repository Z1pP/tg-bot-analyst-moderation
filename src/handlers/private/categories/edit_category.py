import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from container import container
from exceptions.category import CategoryNotFoundError
from keyboards.inline.templates import templates_menu_ikb
from states import CategoryStateManager, TemplateStateManager
from usecases.categories import UpdateCategoryNameUseCase
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    CategoryStateManager.confirm_category_edit,
    F.data == "conf_edit_category",
)
async def confirm_category_edit_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    await callback.answer()

    data = await state.get_data()
    category_id = data.get("category_id")
    old_name = data.get("old_name")
    new_name = data.get("category_name")

    try:
        usecase: UpdateCategoryNameUseCase = container.resolve(
            UpdateCategoryNameUseCase
        )
        category = await usecase.execute(category_id=category_id, new_name=new_name)
        text = f"✅ Категория <b>{old_name}</b> успешно изменена на <b>{category.name}</b>.\n"
    except CategoryNotFoundError as e:
        text = e.get_user_message()
    except Exception as e:
        logger.error("Ошибка при изменении категории: %s", e, exc_info=True)
        text = "⚠️ Произошла ошибка при изменении категории."

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=templates_menu_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=TemplateStateManager.templates_menu,
    )
