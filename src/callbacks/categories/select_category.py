import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from states.response_state import QuickResponseStateManager

router = Router(name=__name__)

logger = logging.getLogger(__name__)


@router.callback_query(
    QuickResponseStateManager.process_template_category,
    F.data.startswith("category__"),
)
async def select_category_for_template_callback(
    query: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обрабчик выбора категории при создании нового шаблона"""

    category_id = query.data.split("__")[1]

    logger.info(
        "Была выбрана категория id=%s пользователем - %s",
        category_id,
        query.from_user.username,
    )

    # Сохраняем выбранную категорию в состоянии
    await state.update_data(category_id=category_id)

    text = "Введите название шаблона:"

    await query.message.answer(text=text)

    await state.set_state(QuickResponseStateManager.process_template_title)

    await query.answer()
