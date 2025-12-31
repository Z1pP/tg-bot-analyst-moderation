import logging

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext

from container import container
from dto import CreateCategoryDTO
from exceptions.category import CategoryAlreadyExists
from keyboards.inline.templates import templates_menu_ikb
from states import CategoryStateManager, TemplateStateManager
from usecases.categories import CreateCategoryUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    CategoryStateManager.confirm_category_creation,
    F.data == "conf_add_category",
)
async def confirm_category_creation_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Обработчик подтверждения создания категории"""
    await callback.answer()

    data = await state.get_data()
    category_name = data.get("category_name")

    try:
        usecase: CreateCategoryUseCase = container.resolve(CreateCategoryUseCase)
        category = await usecase.execute(
            dto=CreateCategoryDTO(name=category_name),
            admin_tg_id=str(callback.from_user.id),
        )
        text = (
            f"✅ Категория <b>{category.name}</b> успешно создана.\n"
            "Теперь вы можете создавать шаблоны в этой категории."
        )
    except CategoryAlreadyExists as e:
        text = e.get_user_message()
    except Exception as e:
        logger.error("Ошибка при создании категории: %s", e, exc_info=True)
        text = "⚠️ Произошла ошибка при создании категории."

    await safe_edit_message(
        bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=templates_menu_ikb(),
    )

    await state.set_state(TemplateStateManager.templates_menu)
